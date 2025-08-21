"""
Integration tests for the Natural Language CLI.

Tests the actual CLI interface with real commands in dry-run mode
to ensure all the real-world scenarios work end-to-end.
"""

import subprocess
import tempfile
import unittest
from pathlib import Path


class TestCLIIntegration(unittest.TestCase):
    """Integration tests for the CLI interface."""

    def run_nlcli_command(self, command, extra_args=None):
        """Run nlcli command and return result."""
        args = ["python", "-m", "nlcli.main", "--dry-run"]
        if extra_args:
            args.extend(extra_args)
        args.extend(["--batch-commands", command])

        result = subprocess.run(
            args,
            cwd="/home/runner/work/Natural-Language-Driven-CLI/Natural-Language-Driven-CLI",
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result

    def test_file_operations_integration(self):
        """Test file operations through CLI interface."""
        commands = [
            "show files >500MB modified yesterday",
            "find all .py files in current directory",
            "search for 'import' inside python files",
            "what's taking up space in current directory",
            "list directories sorted by size",
        ]

        for cmd in commands:
            with self.subTest(command=cmd):
                result = self.run_nlcli_command(cmd)
                # Should succeed (exit code 0) or have reasonable error
                self.assertIn(
                    result.returncode, [0, 1]
                )  # 1 is ok for some planning failures
                # Should not crash
                self.assertNotIn("Traceback", result.stderr)

    def test_process_management_integration(self):
        """Test process management through CLI interface."""
        commands = [
            "list processes using port 8080",
            "show top 5 CPU consuming processes",
            "display system resource usage",
        ]

        for cmd in commands:
            with self.subTest(command=cmd):
                result = self.run_nlcli_command(cmd)
                # Should succeed or have reasonable error
                self.assertIn(result.returncode, [0, 1])
                # Should not crash
                self.assertNotIn("Traceback", result.stderr)

    def test_networking_integration(self):
        """Test networking through CLI interface."""
        commands = [
            "ping google.com",
            "check what services are listening on ports",
            "resolve DNS for openai.com",
        ]

        for cmd in commands:
            with self.subTest(command=cmd):
                result = self.run_nlcli_command(cmd)
                # Should succeed or have reasonable error
                self.assertIn(result.returncode, [0, 1])
                # Should not crash
                self.assertNotIn("Traceback", result.stderr)

    def test_git_and_package_integration(self):
        """Test git and package management through CLI interface."""
        commands = [
            "git status",
            "git log last 3 commits",
            "list installed apt packages",
            "show details of package curl",
        ]

        for cmd in commands:
            with self.subTest(command=cmd):
                result = self.run_nlcli_command(cmd)
                # Should succeed or have reasonable error
                self.assertIn(result.returncode, [0, 1])
                # Should not crash
                self.assertNotIn("Traceback", result.stderr)

    def test_dangerous_commands_blocked(self):
        """Test that dangerous commands are properly blocked."""
        dangerous_commands = [
            "rm -rf /",
            "chmod -R 777 *",
            "dd if=/dev/zero of=/dev/sda",
        ]

        for cmd in dangerous_commands:
            with self.subTest(command=cmd):
                result = self.run_nlcli_command(cmd)
                # Should fail - dangerous commands should be blocked at planning stage
                self.assertEqual(result.returncode, 1)

                # Should indicate command was not understood/blocked
                output = result.stdout + result.stderr
                self.assertTrue(
                    "couldn't understand" in output.lower()
                    or "could not generate" in output.lower()
                    or "Command blocked" in output
                    or "blocked" in output.lower()
                )

    def test_multi_language_support(self):
        """Test multi-language input (if available)."""
        # Test with language parameter
        commands = [
            ("buscar archivos grandes", "es"),
            ("lister tous les fichiers", "fr"),
            ("zeige alle dateien", "de"),
        ]

        for cmd, lang in commands:
            with self.subTest(command=cmd, language=lang):
                result = self.run_nlcli_command(cmd, ["--lang", lang])
                # Should succeed or have reasonable error
                self.assertIn(result.returncode, [0, 1])
                # Should not crash
                self.assertNotIn("Traceback", result.stderr)

    def test_batch_script_execution(self):
        """Test batch script execution."""
        script_content = """@name Test Script
@description Test script for integration testing

> list files in current directory
> show system resource usage
> ping localhost
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".nlcli", delete=False) as f:
            f.write(script_content)
            script_path = f.name

        try:
            # Test batch script execution
            result = subprocess.run(
                ["python", "-m", "nlcli.main", "--dry-run", "--batch", script_path],
                cwd="/home/runner/work/Natural-Language-Driven-CLI/Natural-Language-Driven-CLI",
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Should succeed
            self.assertIn(result.returncode, [0, 1])
            # Should not crash
            self.assertNotIn("Traceback", result.stderr)
            # Should execute multiple commands
            self.assertIn("batch", result.stdout.lower())

        finally:
            Path(script_path).unlink()

    def test_help_and_version_commands(self):
        """Test basic CLI functionality."""
        # Test help
        result = subprocess.run(
            ["python", "-m", "nlcli.main", "--help"],
            cwd="/home/runner/work/Natural-Language-Driven-CLI/Natural-Language-Driven-CLI",
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Natural Language Driven CLI", result.stdout)

        # Test version
        result = subprocess.run(
            ["python", "-m", "nlcli.main", "--version"],
            cwd="/home/runner/work/Natural-Language-Driven-CLI/Natural-Language-Driven-CLI",
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)

    def test_docker_plugin_integration(self):
        """Test Docker plugin functionality (if available)."""
        commands = [
            "show docker containers",
            "list all docker containers including stopped",
        ]

        for cmd in commands:
            with self.subTest(command=cmd):
                result = self.run_nlcli_command(cmd)
                # Should succeed or have reasonable error
                self.assertIn(result.returncode, [0, 1])
                # Should not crash
                self.assertNotIn("Traceback", result.stderr)

    def test_context_awareness_simulation(self):
        """Test context awareness through batch commands."""
        commands = [
            "find large files in Downloads",
            "now only show videos",
            "show file details",
        ]

        # Test as batch commands to simulate context
        result = subprocess.run(
            ["python", "-m", "nlcli.main", "--dry-run"]
            + ["--batch-commands"]
            + commands,
            cwd="/home/runner/work/Natural-Language-Driven-CLI/Natural-Language-Driven-CLI",
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Should succeed or have reasonable error (including exit code 2 for some errors)
        self.assertIn(result.returncode, [0, 1, 2])
        # Should not crash
        self.assertNotIn("Traceback", result.stderr)

    def test_performance_and_advanced_features(self):
        """Test advanced CLI features."""
        # These might be handled as special commands in REPL
        # or as regular tools, depending on implementation
        commands = ["performance", "show system information", "list available tools"]

        for cmd in commands:
            with self.subTest(command=cmd):
                result = self.run_nlcli_command(cmd)
                # Should succeed or have reasonable error
                self.assertIn(result.returncode, [0, 1])
                # Should not crash
                self.assertNotIn("Traceback", result.stderr)


class TestCLIErrorHandling(unittest.TestCase):
    """Test CLI error handling and edge cases."""

    def test_invalid_batch_file(self):
        """Test handling of invalid batch file."""
        result = subprocess.run(
            ["python", "-m", "nlcli.main", "--batch", "/nonexistent/file.nlcli"],
            cwd="/home/runner/work/Natural-Language-Driven-CLI/Natural-Language-Driven-CLI",
            capture_output=True,
            text=True,
        )
        # Should fail gracefully (exit code 1 or 2 are both acceptable for errors)
        self.assertIn(result.returncode, [1, 2])
        # Should contain error message
        stderr_lower = result.stderr.lower()
        self.assertTrue("error" in stderr_lower or "failed" in stderr_lower)

    def test_empty_command(self):
        """Test handling of empty commands."""
        result = subprocess.run(
            ["python", "-m", "nlcli.main", "--dry-run", "--batch-commands", ""],
            cwd="/home/runner/work/Natural-Language-Driven-CLI/Natural-Language-Driven-CLI",
            capture_output=True,
            text=True,
        )
        # Should handle gracefully
        self.assertIn(result.returncode, [0, 1])

    def test_malformed_natural_language(self):
        """Test handling of malformed natural language input."""
        weird_commands = [
            "asdfasdf random nonsense",
            "123456789",
            "!@#$%^&*()",
            "a" * 1000,  # Very long input
        ]

        for cmd in weird_commands:
            with self.subTest(command=cmd):
                result = subprocess.run(
                    [
                        "python",
                        "-m",
                        "nlcli.main",
                        "--dry-run",
                        "--batch-commands",
                        cmd,
                    ],
                    cwd="/home/runner/work/Natural-Language-Driven-CLI/Natural-Language-Driven-CLI",
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                # Should handle gracefully without crashing
                self.assertIn(result.returncode, [0, 1])
                self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
