"""
Test Plugin System
Tests for plugin discovery, loading, and management.
"""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nlcli.plugins import PluginManager, PluginMetadata, LoadedPlugin, create_example_plugin, get_plugin_manager
from nlcli.registry import ToolSchema, ToolArg


class TestPluginSystem(unittest.TestCase):
    """Test plugin system functionality."""
    
    def setUp(self):
        self.plugin_manager = PluginManager()
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        # Clean up temp directory
        if self.temp_dir.exists():
            import shutil
            shutil.rmtree(self.temp_dir)
    
    def test_plugin_metadata(self):
        """Test plugin metadata creation."""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author"
        )
        
        self.assertEqual(metadata.name, "test_plugin")
        self.assertEqual(metadata.version, "1.0.0")
        self.assertEqual(metadata.dependencies, [])
    
    def test_plugin_manager_initialization(self):
        """Test plugin manager initializes correctly."""
        manager = PluginManager()
        self.assertIsInstance(manager.plugins, dict)
        self.assertIsInstance(manager.plugin_paths, list)
        self.assertTrue(len(manager.plugin_paths) >= 1)  # At least user plugin dir
    
    def test_add_plugin_path(self):
        """Test adding custom plugin paths."""
        initial_count = len(self.plugin_manager.plugin_paths)
        self.plugin_manager.add_plugin_path(self.temp_dir)
        
        self.assertEqual(len(self.plugin_manager.plugin_paths), initial_count + 1)
        self.assertIn(self.temp_dir, self.plugin_manager.plugin_paths)
    
    def test_create_example_plugin(self):
        """Test example plugin creation."""
        example_content = create_example_plugin()
        
        self.assertIn("def get_tools()", example_content)
        self.assertIn("def get_plugin_info()", example_content)
        self.assertIn("ToolSchema", example_content)
    
    def test_discover_plugins_empty(self):
        """Test plugin discovery with no plugins."""
        manager = PluginManager()
        manager.plugin_paths = [self.temp_dir]
        
        plugins = manager.discover_plugins()
        self.assertEqual(len(plugins), 0)
    
    def test_discover_plugins_with_files(self):
        """Test plugin discovery with plugin files."""
        # Create a test plugin file
        plugin_file = self.temp_dir / "test_plugin.py"
        plugin_file.write_text(create_example_plugin())
        
        manager = PluginManager()
        manager.plugin_paths = [self.temp_dir]
        
        plugins = manager.discover_plugins()
        self.assertEqual(len(plugins), 1)
        self.assertEqual(plugins[0], plugin_file)
    
    def test_load_valid_plugin(self):
        """Test loading a valid plugin."""
        # Create a test plugin file
        plugin_file = self.temp_dir / "test_plugin.py"
        plugin_content = '''
from nlcli.registry import ToolSchema, ToolArg

def get_tools():
    return [
        ToolSchema(
            name="test_tool",
            summary="Test tool",
            args={},
            generator={"cmd": "echo test"},
            danger_level="read_only",
            keywords=["test"]
        )
    ]

def get_plugin_info():
    return {
        "name": "test_plugin",
        "version": "1.0.0",
        "description": "Test plugin",
        "author": "Test Author"
    }
'''
        plugin_file.write_text(plugin_content)
        
        loaded_plugin = self.plugin_manager.load_plugin(plugin_file)
        
        self.assertIsNotNone(loaded_plugin)
        self.assertEqual(loaded_plugin.metadata.name, "test_plugin")
        self.assertEqual(len(loaded_plugin.tools), 1)
        self.assertTrue(loaded_plugin.enabled)
        
        # Check tool was namespaced
        self.assertEqual(loaded_plugin.tools[0].name, "test_plugin_test_tool")
    
    def test_load_invalid_plugin(self):
        """Test loading an invalid plugin."""
        # Create an invalid plugin file
        plugin_file = self.temp_dir / "invalid_plugin.py"
        plugin_file.write_text("print('This is not a valid plugin')")
        
        loaded_plugin = self.plugin_manager.load_plugin(plugin_file)
        self.assertIsNone(loaded_plugin)
    
    def test_plugin_enable_disable(self):
        """Test enabling and disabling plugins."""
        # Create and load a test plugin
        plugin_file = self.temp_dir / "test_plugin.py"
        plugin_file.write_text(create_example_plugin())
        
        loaded_plugin = self.plugin_manager.load_plugin(plugin_file)
        self.assertIsNotNone(loaded_plugin)
        
        plugin_name = loaded_plugin.metadata.name
        
        # Test disable
        result = self.plugin_manager.disable_plugin(plugin_name)
        self.assertTrue(result)
        self.assertFalse(self.plugin_manager.plugins[plugin_name].enabled)
        
        # Test enable
        result = self.plugin_manager.enable_plugin(plugin_name)
        self.assertTrue(result)
        self.assertTrue(self.plugin_manager.plugins[plugin_name].enabled)
    
    def test_get_all_tools(self):
        """Test getting all tools from plugins."""
        # Initially no plugin tools
        tools = self.plugin_manager.get_all_tools()
        self.assertEqual(len(tools), 0)
        
        # Load a plugin
        plugin_file = self.temp_dir / "test_plugin.py"
        plugin_file.write_text(create_example_plugin())
        loaded_plugin = self.plugin_manager.load_plugin(plugin_file)
        
        # Now should have plugin tools
        tools = self.plugin_manager.get_all_tools()
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0].name, "example_hello_world")
    
    def test_get_plugin_list(self):
        """Test getting plugin list."""
        # Load a plugin
        plugin_file = self.temp_dir / "test_plugin.py"
        plugin_file.write_text(create_example_plugin())
        self.plugin_manager.load_plugin(plugin_file)
        
        plugin_list = self.plugin_manager.get_plugin_list()
        
        self.assertEqual(len(plugin_list), 1)
        self.assertEqual(plugin_list[0]["name"], "example")
        self.assertEqual(plugin_list[0]["version"], "1.0.0")
        self.assertTrue(plugin_list[0]["enabled"])
        self.assertEqual(plugin_list[0]["tools_count"], 1)
    
    def test_global_plugin_manager(self):
        """Test global plugin manager singleton."""
        manager1 = get_plugin_manager()
        manager2 = get_plugin_manager()
        
        self.assertIs(manager1, manager2)
    
    @patch.dict('os.environ', {'NLCLI_PLUGIN_PATH': '/custom/path'})
    def test_environment_plugin_path(self):
        """Test plugin path from environment variable."""
        with patch('pathlib.Path.exists', return_value=True):
            manager = PluginManager()
            # Should include the custom path from environment
            path_strings = [str(p) for p in manager.plugin_paths]
            self.assertIn('/custom/path', path_strings)


if __name__ == '__main__':
    unittest.main()