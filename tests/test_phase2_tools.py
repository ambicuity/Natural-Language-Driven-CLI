"""
Tests for Phase 2 Extended Tools functionality.
Tests process management, network operations, package management, and git tools.
"""

import unittest
from unittest.mock import Mock, patch  # noqa: F401

from nlcli.registry import ToolRegistry
from nlcli.tools.git_tools import get_git_tools
from nlcli.tools.network_tools import get_network_tools
from nlcli.tools.package_tools import get_package_tools
from nlcli.tools.process_tools import get_process_tools


class TestPhase2Tools(unittest.TestCase):
    """Test Phase 2 extended tools."""

    def setUp(self):
        self.registry = ToolRegistry()

    def test_process_tools_loaded(self):
        """Test that process management tools are loaded."""
        process_tools = get_process_tools()
        self.assertTrue(len(process_tools) > 0)

        tool_names = [tool.name for tool in process_tools]
        expected_tools = [
            "list_processes",
            "kill_process",
            "process_by_port",
            "process_tree",
            "system_resources",
        ]

        for expected in expected_tools:
            self.assertIn(expected, tool_names)

    def test_network_tools_loaded(self):
        """Test that network tools are loaded."""
        network_tools = get_network_tools()
        self.assertTrue(len(network_tools) > 0)

        tool_names = [tool.name for tool in network_tools]
        expected_tools = [
            "ping_host",
            "http_request",
            "network_connections",
            "dns_lookup",
            "download_file",
            "network_interfaces",
        ]

        for expected in expected_tools:
            self.assertIn(expected, tool_names)

    def test_package_tools_loaded(self):
        """Test that package management tools are loaded."""
        package_tools = get_package_tools()
        self.assertTrue(len(package_tools) > 0)

        tool_names = [tool.name for tool in package_tools]
        expected_tools = [
            "brew_search",
            "brew_info",
            "brew_list",
            "apt_search",
            "apt_info",
            "apt_list",
        ]

        for expected in expected_tools:
            self.assertIn(expected, tool_names)

    def test_git_tools_loaded(self):
        """Test that git tools are loaded."""
        git_tools = get_git_tools()
        self.assertTrue(len(git_tools) > 0)

        tool_names = [tool.name for tool in git_tools]
        expected_tools = [
            "git_status",
            "git_log",
            "git_diff",
            "git_branch",
            "git_show",
            "git_remote",
            "git_blame",
        ]

        for expected in expected_tools:
            self.assertIn(expected, tool_names)

    def test_process_command_generation(self):
        """Test process management command generation."""
        tool = self.registry.get_tool("list_processes")

        # Test basic process listing
        args = {"sort": "cpu", "limit": 10}
        command = self.registry.generate_command(tool, args)
        self.assertIn("ps aux", command)
        self.assertIn("head -10", command)

        # Test process by port
        tool = self.registry.get_tool("process_by_port")
        args = {"port": 3000}
        command = self.registry.generate_command(tool, args)
        self.assertIn("lsof -i :3000", command)

    def test_network_command_generation(self):
        """Test network tools command generation."""
        # Test ping command
        tool = self.registry.get_tool("ping_host")
        args = {"host": "google.com", "count": 5}
        command = self.registry.generate_command(tool, args)
        self.assertIn("ping -c 5", command)
        self.assertIn("google.com", command)

        # Test network connections
        tool = self.registry.get_tool("network_connections")
        args = {"listening": True, "process": True}
        command = self.registry.generate_command(tool, args)
        self.assertIn("ss", command)
        self.assertIn("-l", command)
        self.assertIn("-p", command)

    def test_package_command_generation(self):
        """Test package management command generation."""
        # Test brew search
        tool = self.registry.get_tool("brew_search")
        args = {"package": "python"}
        command = self.registry.generate_command(tool, args)
        self.assertIn("brew search python", command)

        # Test apt info
        tool = self.registry.get_tool("apt_info")
        args = {"package": "nginx"}
        command = self.registry.generate_command(tool, args)
        self.assertIn("apt show nginx", command)

    def test_git_command_generation(self):
        """Test git command generation."""
        # Test git status
        tool = self.registry.get_tool("git_status")
        args = {"short": False}
        command = self.registry.generate_command(tool, args)
        self.assertEqual(command, "git status")

        # Test git log
        tool = self.registry.get_tool("git_log")
        args = {"limit": 5, "oneline": True}
        command = self.registry.generate_command(tool, args)
        self.assertIn("git log --oneline -5", command)

        # Test git diff with file
        tool = self.registry.get_tool("git_diff")
        args = {"file": "README.md", "staged": False}
        command = self.registry.generate_command(tool, args)
        self.assertIn("git diff README.md", command)

    def test_tool_matching_for_phase2(self):
        """Test that natural language input matches Phase 2 tools correctly."""
        # Test process management matching
        matches = self.registry.find_matching_tools("list running processes")
        self.assertTrue(len(matches) > 0)
        best_tool, _ = matches[0]
        self.assertEqual(best_tool.name, "list_processes")

        # Test network tools matching
        matches = self.registry.find_matching_tools("ping google.com")
        self.assertTrue(len(matches) > 0)
        best_tool, _ = matches[0]
        self.assertEqual(best_tool.name, "ping_host")

        # Test package tools matching
        matches = self.registry.find_matching_tools("brew search docker")
        self.assertTrue(len(matches) > 0)
        best_tool, _ = matches[0]
        self.assertEqual(best_tool.name, "brew_search")

        # Test git tools matching
        matches = self.registry.find_matching_tools("git status")
        self.assertTrue(len(matches) > 0)
        best_tool, _ = matches[0]
        self.assertEqual(best_tool.name, "git_status")

    def test_danger_levels(self):
        """Test that tools have appropriate danger levels."""
        # Read-only tools should be safe
        safe_tools = [
            "list_processes",
            "ping_host",
            "git_status",
            "brew_search",
            "apt_search",
        ]
        for tool_name in safe_tools:
            tool = self.registry.get_tool(tool_name)
            self.assertEqual(tool.danger_level, "read_only")

        # Some tools should be more dangerous
        dangerous_tools = ["kill_process"]
        for tool_name in dangerous_tools:
            tool = self.registry.get_tool(tool_name)
            self.assertIn(tool.danger_level, ["destructive", "modify"])

    def test_tool_examples(self):
        """Test that tools have proper examples."""
        all_tools = (
            get_process_tools()
            + get_network_tools()
            + get_package_tools()
            + get_git_tools()
        )

        for tool in all_tools:
            self.assertTrue(
                len(tool.examples) > 0, f"Tool {tool.name} should have examples"
            )
            for example in tool.examples:
                self.assertIn(
                    "nl", example, f"Example for {tool.name} should have 'nl' key"
                )
                self.assertIn(
                    "args", example, f"Example for {tool.name} should have 'args' key"
                )

    def test_tool_keywords(self):
        """Test that tools have appropriate keywords for matching."""
        all_tools = (
            get_process_tools()
            + get_network_tools()
            + get_package_tools()
            + get_git_tools()
        )

        for tool in all_tools:
            self.assertTrue(
                len(tool.keywords) > 0, f"Tool {tool.name} should have keywords"
            )
            self.assertIsInstance(
                tool.keywords, list, f"Tool {tool.name} keywords should be a list"
            )


if __name__ == "__main__":
    unittest.main()
