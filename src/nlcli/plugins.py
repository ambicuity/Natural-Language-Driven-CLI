"""
Plugin SDK and Loading System
Supports dynamic loading of external plugins with validation and security.
"""

import importlib
import importlib.util
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from nlcli.registry import ToolSchema


@runtime_checkable
class PluginInterface(Protocol):
    """Protocol that all plugins must implement."""

    def get_tools(self) -> List[ToolSchema]:
        """Return list of tools provided by this plugin."""
        ...

    def get_plugin_info(self) -> Dict[str, Any]:
        """Return plugin metadata."""
        ...


@dataclass
class PluginMetadata:
    """Plugin metadata."""

    name: str
    version: str
    description: str
    author: str
    website: Optional[str] = None
    dependencies: List[str] = None
    min_nlcli_version: str = "0.1.0"

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class LoadedPlugin:
    """Represents a loaded plugin."""

    metadata: PluginMetadata
    module: Any
    tools: List[ToolSchema]
    enabled: bool = True


class PluginManager:
    """Manages plugin discovery, loading, and lifecycle."""

    def __init__(self):
        self.plugins: Dict[str, LoadedPlugin] = {}
        self.plugin_paths: List[Path] = []
        self.logger = logging.getLogger(__name__)

        # Default plugin search paths
        self._setup_default_paths()

    def _setup_default_paths(self) -> None:
        """Setup default plugin search paths."""
        # User plugins directory
        user_plugins = Path.home() / ".nlcli" / "plugins"
        user_plugins.mkdir(parents=True, exist_ok=True)
        self.plugin_paths.append(user_plugins)

        # System plugins directory
        system_plugins = Path("/usr/local/share/nlcli/plugins")
        if system_plugins.exists():
            self.plugin_paths.append(system_plugins)

        # Environment variable override
        if "NLCLI_PLUGIN_PATH" in os.environ:
            for path_str in os.environ["NLCLI_PLUGIN_PATH"].split(":"):
                plugin_path = Path(path_str)
                if plugin_path.exists():
                    self.plugin_paths.append(plugin_path)

    def add_plugin_path(self, path: Path) -> None:
        """Add a custom plugin search path."""
        if path.exists() and path.is_dir():
            self.plugin_paths.append(path)

    def discover_plugins(self) -> List[Path]:
        """Discover available plugins."""
        plugin_files = []

        for plugin_path in self.plugin_paths:
            if not plugin_path.exists():
                continue

            # Look for Python files and packages
            for item in plugin_path.iterdir():
                if item.is_file() and item.suffix == ".py":
                    plugin_files.append(item)
                elif item.is_dir() and (item / "__init__.py").exists():
                    plugin_files.append(item / "__init__.py")

        return plugin_files

    def load_plugin(self, plugin_path: Path) -> Optional[LoadedPlugin]:
        """Load a single plugin from path."""
        try:
            # Generate module name from path
            module_name = f"nlcli_plugin_{plugin_path.stem}"

            # Load the module
            spec = importlib.util.spec_from_file_location(module_name, plugin_path)
            if spec is None or spec.loader is None:
                self.logger.error(f"Could not create spec for plugin: {plugin_path}")
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Validate plugin interface
            if not hasattr(module, "get_tools") or not hasattr(
                module, "get_plugin_info"
            ):
                self.logger.error(f"Plugin {plugin_path} missing required functions")
                return None

            # Get plugin info and tools
            plugin_info = module.get_plugin_info()
            metadata = PluginMetadata(**plugin_info)

            tools = module.get_tools()
            if not isinstance(tools, list):
                self.logger.error(
                    f"Plugin {plugin_path} get_tools() must return a list"
                )
                return None

            # Validate all tools
            validated_tools = []
            for tool in tools:
                if isinstance(tool, ToolSchema):
                    # Add plugin namespace to tool name to avoid conflicts
                    tool.name = f"{metadata.name}_{tool.name}"
                    validated_tools.append(tool)
                else:
                    self.logger.warning(
                        f"Invalid tool in plugin {metadata.name}: {tool}"
                    )

            loaded_plugin = LoadedPlugin(
                metadata=metadata, module=module, tools=validated_tools
            )

            self.plugins[metadata.name] = loaded_plugin
            self.logger.info(f"Loaded plugin: {metadata.name} v{metadata.version}")

            return loaded_plugin

        except Exception as e:
            self.logger.error(f"Failed to load plugin {plugin_path}: {e}")
            return None

    def load_all_plugins(self) -> None:
        """Discover and load all available plugins."""
        plugin_files = self.discover_plugins()

        for plugin_file in plugin_files:
            self.load_plugin(plugin_file)

        self.logger.info(f"Loaded {len(self.plugins)} plugins")

    def get_plugin(self, name: str) -> Optional[LoadedPlugin]:
        """Get a loaded plugin by name."""
        return self.plugins.get(name)

    def get_all_tools(self) -> List[ToolSchema]:
        """Get all tools from all loaded plugins."""
        all_tools = []
        for plugin in self.plugins.values():
            if plugin.enabled:
                all_tools.extend(plugin.tools)
        return all_tools

    def enable_plugin(self, name: str) -> bool:
        """Enable a plugin."""
        if name in self.plugins:
            self.plugins[name].enabled = True
            return True
        return False

    def disable_plugin(self, name: str) -> bool:
        """Disable a plugin."""
        if name in self.plugins:
            self.plugins[name].enabled = False
            return True
        return False

    def unload_plugin(self, name: str) -> bool:
        """Unload a plugin completely."""
        if name in self.plugins:
            del self.plugins[name]
            return True
        return False

    def get_plugin_list(self) -> List[Dict[str, Any]]:
        """Get list of all plugins with their status."""
        plugin_list = []
        for name, plugin in self.plugins.items():
            plugin_list.append(
                {
                    "name": name,
                    "version": plugin.metadata.version,
                    "description": plugin.metadata.description,
                    "author": plugin.metadata.author,
                    "tools_count": len(plugin.tools),
                    "enabled": plugin.enabled,
                }
            )
        return plugin_list


# Global plugin manager instance
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager instance."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


def create_example_plugin() -> str:
    """Create an example plugin file for development."""
    example_plugin = '''"""
Example NLCLI Plugin
This is a template showing how to create a plugin for Natural Language CLI.
"""
from nlcli.registry import ToolSchema, ToolArg


def get_tools():
    """Return list of tools provided by this plugin."""
    return [
        ToolSchema(
            name="hello_world",
            summary="Say hello to the world",
            args={
                "name": ToolArg(
                    "name", "string", default="World", description="Name to greet"
                )
            },
            generator={
                "cmd": "echo 'Hello, {name}!'"
            },
            danger_level="read_only",
            examples=[
                {"nl": "say hello", "args": {"name": "World"}},
                {"nl": "greet Alice", "args": {"name": "Alice"}}
            ],
            keywords=["hello", "greet", "say"]
        )
    ]


def get_plugin_info():
    """Return plugin metadata."""
    return {
        "name": "example",
        "version": "1.0.0",
        "description": "Example plugin demonstrating NLCLI plugin development",
        "author": "NLCLI Team",
        "website": "https://github.com/ambicuity/Natural-Language-Driven-CLI",
        "dependencies": [],
        "min_nlcli_version": "0.1.0"
    }
'''
    return example_plugin
