# Plugin Development

NLCLI's plugin system allows you to add custom tools and extend functionality for your specific needs.

## Quick Start

1. Create a Python file in `~/.nlcli/plugins/`
2. Define your tools using the `ToolSchema` class
3. Implement `get_plugin_info()` and `get_my_tools()` functions
4. Restart NLCLI or use `› reload plugins`

## Example Plugin

Create `~/.nlcli/plugins/docker_plugin.py`:

```python
from nlcli.registry import ToolSchema, ToolArg

def get_my_tools():
    """Return list of tools provided by this plugin."""
    return [
        ToolSchema(
            name="docker_ps",
            summary="List Docker containers",
            args={
                "all": ToolArg("all", "boolean", default=False)
            },
            generator={
                "cmd": "docker ps {all_flag}",
                "clauses": {"all_flag": "-a"}
            },
            danger_level="read_only",
            examples=[
                {"nl": "show docker containers", "args": {"all": False}},
                {"nl": "list all containers including stopped", "args": {"all": True}}
            ],
            keywords=["docker", "containers", "ps"]
        ),
        ToolSchema(
            name="docker_logs",
            summary="Show logs for a Docker container",
            args={
                "container": ToolArg("container", "string", required=True),
                "follow": ToolArg("follow", "boolean", default=False),
                "tail": ToolArg("tail", "number", default=100)
            },
            generator={
                "cmd": "docker logs {follow_flag} --tail {tail} {container}",
                "clauses": {"follow_flag": "-f"}
            },
            danger_level="read_only",
            examples=[
                {"nl": "show logs for nginx container", "args": {"container": "nginx"}},
                {"nl": "follow logs for web app", "args": {"container": "webapp", "follow": True}}
            ],
            keywords=["docker", "logs", "container"]
        )
    ]

def get_plugin_info():
    """Return plugin metadata."""
    return {
        "name": "docker",
        "version": "1.0.0",
        "description": "Docker container management tools",
        "author": "Your Name",
        "license": "Apache 2.0"
    }
```

## ToolSchema Reference

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique tool identifier |
| `summary` | string | Brief description of what the tool does |
| `args` | dict | Dictionary of tool arguments |
| `generator` | dict | Command generation configuration |
| `danger_level` | string | Safety level: `"read_only"`, `"safe"`, `"destructive"` |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `examples` | list | List of natural language examples |
| `keywords` | list | Keywords for semantic matching |
| `requires_confirmation` | bool | Force confirmation prompt |
| `timeout` | number | Custom timeout in seconds |

### ToolArg Reference

```python
ToolArg(
    name="argument_name",
    type="string|number|boolean|array",
    required=False,
    default=None,
    description="Argument description",
    validation=None  # Optional validation function
)
```

### Generator Configuration

```python
generator = {
    "cmd": "command {arg1} {flag} {arg2}",
    "clauses": {
        "flag": "--flag-value"  # Conditional flags
    },
    "conditions": {
        "arg1": "arg1 != ''"     # When to include arg1
    }
}
```

## Advanced Plugin Example

```python
from nlcli.registry import ToolSchema, ToolArg
import os
import subprocess

def get_my_tools():
    return [
        # Custom file search with advanced features
        ToolSchema(
            name="advanced_find",
            summary="Advanced file search with custom filters",
            args={
                "pattern": ToolArg("pattern", "string", required=True),
                "path": ToolArg("path", "string", default="."),
                "size": ToolArg("size", "string", default=""),
                "modified": ToolArg("modified", "string", default=""),
                "type": ToolArg("type", "string", default="f"),
                "exclude": ToolArg("exclude", "array", default=[])
            },
            generator={
                "cmd": "find {path} -type {type} -name '{pattern}' {size_clause} {modified_clause} {exclude_clause}",
                "clauses": {
                    "size_clause": "-size {size}",
                    "modified_clause": "-mtime {modified}",
                    "exclude_clause": "-not -path '{exclude_pattern}'"
                },
                "conditions": {
                    "size_clause": "size != ''",
                    "modified_clause": "modified != ''",
                    "exclude_clause": "len(exclude) > 0"
                }
            },
            danger_level="read_only",
            examples=[
                {
                    "nl": "find large Python files modified recently",
                    "args": {
                        "pattern": "*.py",
                        "size": "+1M",
                        "modified": "-7"
                    }
                }
            ],
            keywords=["find", "search", "files", "advanced"]
        ),

        # Custom system monitoring
        ToolSchema(
            name="system_health",
            summary="Show comprehensive system health information",
            args={},
            generator={
                "cmd": "echo 'CPU Usage:' && top -bn1 | grep 'Cpu(s)' && echo 'Memory Usage:' && free -h && echo 'Disk Usage:' && df -h",
                "clauses": {}
            },
            danger_level="read_only",
            examples=[
                {"nl": "show system health", "args": {}},
                {"nl": "check system status", "args": {}}
            ],
            keywords=["system", "health", "status", "monitoring"]
        )
    ]

def get_plugin_info():
    return {
        "name": "advanced_tools",
        "version": "1.2.0",
        "description": "Advanced system tools and utilities",
        "author": "Advanced User",
        "license": "Apache 2.0",
        "homepage": "https://github.com/user/advanced-nlcli-tools",
        "dependencies": ["findutils", "procps"]
    }

# Optional: Custom initialization
def plugin_init():
    """Called when plugin is loaded."""
    print("Advanced tools plugin loaded!")

# Optional: Custom cleanup
def plugin_cleanup():
    """Called when plugin is unloaded."""
    print("Advanced tools plugin unloaded!")
```

## Plugin Management Commands

```bash
› plugins              # List loaded plugins
› reload plugins       # Reload all plugins
› plugin info docker   # Show info for specific plugin
› plugin disable docker # Disable plugin
› plugin enable docker  # Enable plugin
```

## Testing Your Plugin

1. Create a test file in your plugin directory:

```python
# test_my_plugin.py
import pytest
from my_plugin import get_my_tools, get_plugin_info

def test_plugin_info():
    info = get_plugin_info()
    assert info["name"] == "my_plugin"
    assert "version" in info

def test_tools():
    tools = get_my_tools()
    assert len(tools) > 0
    assert all(hasattr(tool, 'name') for tool in tools)
```

2. Test with NLCLI:

```bash
› reload plugins
› docker ps           # Test your tool
```

## Plugin Distribution

### Local Installation
Place plugin files in `~/.nlcli/plugins/`

### Package Distribution
Create a Python package with plugins in a `nlcli_plugins` namespace:

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="nlcli-docker-plugin",
    packages=find_packages(),
    entry_points={
        'nlcli_plugins': [
            'docker = nlcli_docker_plugin:get_my_tools',
        ],
    },
)
```

## Best Practices

1. **Safety First**: Use appropriate `danger_level` settings
2. **Clear Examples**: Provide comprehensive natural language examples
3. **Good Keywords**: Include relevant keywords for semantic matching
4. **Error Handling**: Consider edge cases in your commands
5. **Documentation**: Document your plugin's functionality
6. **Testing**: Test your plugin thoroughly
7. **Versioning**: Use semantic versioning for your plugins

## Plugin Security

- Plugins run with the same privileges as NLCLI
- Be careful with `destructive` danger levels
- Validate user input in custom generators
- Avoid shell injection vulnerabilities
- Consider using `requires_confirmation=True` for risky operations