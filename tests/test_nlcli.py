"""
Test the core Natural Language CLI functionality.
"""

import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from nlcli.context import Intent, SessionContext
from nlcli.engine import explain, plan_and_generate
from nlcli.executor import execute
from nlcli.registry import ToolArg, ToolRegistry, ToolSchema  # noqa: F401
from nlcli.safety import guard


class TestSessionContext(unittest.TestCase):
    """Test session context management."""

    def setUp(self):
        self.context = SessionContext()

    def test_initial_state(self):
        """Test initial context state."""
        self.assertEqual(self.context.cwd, Path.cwd())
        self.assertEqual(len(self.context.filters), 0)
        self.assertEqual(len(self.context.recent_files), 0)

    def test_add_filter(self):
        """Test adding session filters."""
        self.context.add_filter("min_size", "1GB")
        self.assertEqual(self.context.filters["min_size"], "1GB")

    def test_pronoun_resolution(self):
        """Test pronoun resolution."""
        self.context.recent_files = ["/tmp/file1.txt", "/tmp/file2.txt"]
        resolved = self.context.resolve_pronouns("delete those files")
        self.assertIn("file1.txt", resolved)


class TestToolRegistry(unittest.TestCase):
    """Test tool registry functionality."""

    def setUp(self):
        self.registry = ToolRegistry()

    def test_find_matching_tools(self):
        """Test finding tools that match natural language input."""
        matches = self.registry.find_matching_tools("find large files")
        self.assertTrue(len(matches) > 0)

        # Should find find_files tool
        tool_names = [tool.name for tool, _ in matches]
        self.assertIn("find_files", tool_names)

    def test_extract_size_args(self):
        """Test size argument extraction."""
        tool = self.registry.get_tool("find_files")
        context = {"cwd": "/tmp", "filters": {}}

        args = self.registry.extract_args(tool, "files >1GB", context)
        self.assertEqual(args.get("min_size"), "1G")

    def test_generate_find_command(self):
        """Test command generation."""
        tool = self.registry.get_tool("find_files")
        args = {"path": ".", "min_size": "1G", "modified_within": "7d"}

        command = self.registry.generate_command(tool, args)
        self.assertIn("find", command)
        self.assertIn("-size +1G", command)
        self.assertIn("-mtime -7", command)


class TestEngine(unittest.TestCase):
    """Test the planning and generation engine."""

    def setUp(self):
        self.context = SessionContext()
        self.tools = ToolRegistry()

    def test_plan_and_generate_basic(self):
        """Test basic planning and generation."""
        intent = plan_and_generate("find files >1GB", self.context, self.tools)

        self.assertIsNotNone(intent)
        self.assertEqual(intent.tool_name, "find_files")
        self.assertIn("find", intent.command)

    def test_explain_intent(self):
        """Test explanation generation."""
        intent = Intent(
            tool_name="find_files",
            args={"path": ".", "min_size": "1G"},
            command="find . -type f -size +1G",
            explanation="test explanation",
        )

        explanation = explain(intent)
        self.assertEqual(explanation, "test explanation")


class TestSafety(unittest.TestCase):
    """Test safety mechanisms."""

    def setUp(self):
        self.context = SessionContext()

    def test_safe_command_passes(self):
        """Test that safe commands pass safety checks."""
        intent = Intent(
            tool_name="find_files",
            args={"path": "."},
            command="find . -type f -size +1G",
            explanation="Safe file search",
            danger_level="read_only",
        )

        result = guard(intent, self.context)
        self.assertTrue(result)

    def test_dangerous_command_blocked(self):
        """Test that dangerous commands are blocked."""
        intent = Intent(
            tool_name="dangerous_operation",
            args={},
            command="rm -rf /",
            explanation="Dangerous operation",
            danger_level="destructive",
        )

        # Mock the print function to capture output
        with patch("builtins.print"):
            result = guard(intent, self.context)

        self.assertFalse(result)


class TestExecutor(unittest.TestCase):
    """Test command execution."""

    def setUp(self):
        self.context = SessionContext()

    @patch("subprocess.Popen")
    def test_execute_success(self, mock_popen):
        """Test successful command execution."""
        # Mock subprocess
        mock_process = Mock()
        mock_process.communicate.return_value = ("output", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        result = execute("ls", self.context)

        self.assertTrue(result.success)
        self.assertEqual(result.output, "output")
        self.assertEqual(result.exit_code, 0)

    @patch("subprocess.Popen")
    def test_execute_failure(self, mock_popen):
        """Test failed command execution."""
        # Mock subprocess failure
        mock_process = Mock()
        mock_process.communicate.return_value = ("", "error message")
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        result = execute("invalid_command", self.context)

        self.assertFalse(result.success)
        self.assertEqual(result.error, "error message")
        self.assertEqual(result.exit_code, 1)


if __name__ == "__main__":
    unittest.main()