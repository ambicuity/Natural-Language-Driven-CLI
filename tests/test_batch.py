"""
Test Batch Mode and Scripting
Tests for batch script parsing, execution, and management.
"""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from nlcli.batch import (
    BatchCommand, BatchResult, BatchScript, BatchScriptParser,
    BatchExecutor, BatchModeManager
)
from nlcli.context import SessionContext, Intent, ExecutionResult
from nlcli.registry import ToolRegistry


class TestBatchCommand(unittest.TestCase):
    """Test batch command functionality."""
    
    def test_command_creation(self):
        """Test creating a batch command."""
        command = BatchCommand(
            natural_language="find large files",
            line_number=1,
            timeout=30
        )
        
        self.assertEqual(command.natural_language, "find large files")
        self.assertEqual(command.line_number, 1)
        self.assertEqual(command.timeout, 30)
        self.assertEqual(command.depends_on, [])
        self.assertEqual(command.variables, {})
    
    def test_command_with_dependencies(self):
        """Test command with dependencies."""
        command = BatchCommand(
            natural_language="copy files",
            line_number=2,
            depends_on=[1]
        )
        
        self.assertEqual(command.depends_on, [1])


class TestBatchScriptParser(unittest.TestCase):
    """Test batch script parser."""
    
    def setUp(self):
        self.parser = BatchScriptParser()
    
    def test_parse_simple_script(self):
        """Test parsing a simple script."""
        content = """# Simple script
> find all .txt files
> list directory contents
"""
        script = self.parser.parse_content(content)
        
        self.assertEqual(len(script.commands), 2)
        self.assertEqual(script.commands[0].natural_language, "find all .txt files")
        self.assertEqual(script.commands[1].natural_language, "list directory contents")
    
    def test_parse_script_with_metadata(self):
        """Test parsing script with metadata."""
        content = """@name Test Script
@version 1.0
@description A test script

> find files
"""
        script = self.parser.parse_content(content)
        
        self.assertEqual(script.metadata["name"], "Test Script")
        self.assertEqual(script.metadata["version"], "1.0")
        self.assertEqual(script.metadata["description"], "A test script")
        self.assertEqual(len(script.commands), 1)
    
    def test_parse_script_with_variables(self):
        """Test parsing script with variables."""
        content = """BASE_DIR=/tmp/test
FILE_EXT=.txt

> find ${FILE_EXT} files in ${BASE_DIR}
"""
        script = self.parser.parse_content(content)
        
        self.assertEqual(script.variables["BASE_DIR"], "/tmp/test")
        self.assertEqual(script.variables["FILE_EXT"], ".txt")
        self.assertEqual(len(script.commands), 1)
    
    def test_parse_script_with_modifiers(self):
        """Test parsing script with command modifiers."""
        content = """> find files
timeout: 30
retry: 2

> list files
depends: 2
condition: success
"""
        script = self.parser.parse_content(content)
        
        self.assertEqual(len(script.commands), 2)
        
        # First command
        cmd1 = script.commands[0]
        self.assertEqual(cmd1.timeout, 30)
        self.assertEqual(cmd1.retry_count, 2)
        
        # Second command
        cmd2 = script.commands[1]
        self.assertEqual(cmd2.depends_on, [2])
        self.assertEqual(cmd2.condition, "success")
    
    def test_parse_script_with_command_variables(self):
        """Test parsing script with command-specific variables."""
        content = """> find files
var: TARGET_DIR=/tmp
var: PATTERN=*.txt
"""
        script = self.parser.parse_content(content)
        
        self.assertEqual(len(script.commands), 1)
        cmd = script.commands[0]
        self.assertEqual(cmd.variables["TARGET_DIR"], "/tmp")
        self.assertEqual(cmd.variables["PATTERN"], "*.txt")
    
    def test_parse_empty_script(self):
        """Test parsing empty script."""
        content = """# Empty script
# Just comments
"""
        script = self.parser.parse_content(content)
        
        self.assertEqual(len(script.commands), 0)
        self.assertEqual(len(script.variables), 0)
        self.assertEqual(len(script.metadata), 0)
    
    def test_parse_script_from_file(self):
        """Test parsing script from file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.nlcli', delete=False) as f:
            f.write("> test command\n")
            temp_path = Path(f.name)
        
        try:
            script = self.parser.parse_file(temp_path)
            self.assertEqual(len(script.commands), 1)
            self.assertEqual(script.script_path, temp_path)
        finally:
            temp_path.unlink()
    
    def test_parse_nonexistent_file(self):
        """Test parsing nonexistent file raises error."""
        nonexistent_path = Path("/nonexistent/script.nlcli")
        
        with self.assertRaises(FileNotFoundError):
            self.parser.parse_file(nonexistent_path)


class TestBatchExecutor(unittest.TestCase):
    """Test batch executor."""
    
    def setUp(self):
        self.session_context = Mock(spec=SessionContext)
        self.tool_registry = Mock(spec=ToolRegistry)
        self.llm = Mock()
        self.executor = BatchExecutor(self.session_context, self.tool_registry, self.llm)
    
    def test_build_execution_order_simple(self):
        """Test building execution order for simple script."""
        commands = [
            BatchCommand("command 1", line_number=1),
            BatchCommand("command 2", line_number=2),
            BatchCommand("command 3", line_number=3)
        ]
        
        execution_order = self.executor._build_execution_order(commands)
        
        # Commands with no dependencies should be grouped together
        self.assertEqual(len(execution_order), 1)
        self.assertEqual(len(execution_order[0]), 3)  # All three commands in one group
    
    def test_build_execution_order_with_dependencies(self):
        """Test building execution order with dependencies."""
        commands = [
            BatchCommand("command 1", line_number=1),
            BatchCommand("command 2", line_number=2, depends_on=[1]),
            BatchCommand("command 3", line_number=3, depends_on=[1, 2])
        ]
        
        execution_order = self.executor._build_execution_order(commands)
        
        # First group should have command 1
        self.assertEqual(execution_order[0][0].line_number, 1)
        # Second group should have command 2
        self.assertEqual(execution_order[1][0].line_number, 2)
        # Third group should have command 3
        self.assertEqual(execution_order[2][0].line_number, 3)
    
    def test_dependencies_satisfied(self):
        """Test dependency satisfaction check."""
        command = BatchCommand("test", line_number=3, depends_on=[1, 2])
        
        completed_groups = [
            [BatchCommand("cmd1", line_number=1)],
            [BatchCommand("cmd2", line_number=2)]
        ]
        
        satisfied = self.executor._dependencies_satisfied(command, completed_groups)
        self.assertTrue(satisfied)
        
        # Test with missing dependency
        command_missing_dep = BatchCommand("test", line_number=4, depends_on=[1, 2, 3])
        satisfied = self.executor._dependencies_satisfied(command_missing_dep, completed_groups)
        self.assertFalse(satisfied)
    
    def test_should_execute_conditions(self):
        """Test execution conditions."""
        # Always condition
        command = BatchCommand("test", condition="always")
        self.assertTrue(self.executor._should_execute(command))
        
        # No condition (default always)
        command = BatchCommand("test")
        self.assertTrue(self.executor._should_execute(command))
        
        # Success condition with successful previous result
        self.executor.results = [BatchResult(
            command=BatchCommand("prev"), success=True
        )]
        command = BatchCommand("test", condition="success")
        self.assertTrue(self.executor._should_execute(command))
        
        # Success condition with failed previous result
        self.executor.results = [BatchResult(
            command=BatchCommand("prev"), success=False
        )]
        command = BatchCommand("test", condition="success")
        self.assertFalse(self.executor._should_execute(command))
        
        # Failure condition with failed previous result
        command = BatchCommand("test", condition="failure")
        self.assertTrue(self.executor._should_execute(command))
    
    def test_substitute_variables(self):
        """Test variable substitution."""
        self.executor.variables = {"BASE_DIR": "/tmp", "PATTERN": "*.txt"}
        
        command = BatchCommand(
            natural_language="find ${PATTERN} files in ${BASE_DIR}",
            variables={"LOCAL_VAR": "test"}
        )
        
        processed = self.executor._substitute_variables(command)
        
        expected = "find *.txt files in /tmp"
        self.assertEqual(processed.natural_language, expected)
    
    @patch('nlcli.engine.plan_and_generate')
    @patch('nlcli.executor.execute')
    def test_execute_command_success(self, mock_execute, mock_plan):
        """Test successful command execution."""
        # Mock intent generation
        mock_intent = Mock(spec=Intent)
        mock_intent.command = "ls -la"
        mock_plan.return_value = mock_intent
        
        # Mock execution result
        mock_exec_result = Mock(spec=ExecutionResult)
        mock_exec_result.success = True
        mock_exec_result.output = "file1.txt\nfile2.txt"
        mock_exec_result.error = ""
        mock_exec_result.exit_code = 0
        mock_execute.return_value = mock_exec_result
        
        command = BatchCommand("list files")
        result = self.executor._execute_command(command, dry_run=False)
        
        self.assertTrue(result.success)
        self.assertEqual(result.command.generated_command, "ls -la")
        self.assertEqual(result.output, "file1.txt\nfile2.txt")
    
    @patch('nlcli.engine.plan_and_generate')
    def test_execute_command_plan_failure(self, mock_plan):
        """Test command execution when planning fails."""
        mock_plan.return_value = None
        
        command = BatchCommand("invalid command")
        result = self.executor._execute_command(command, dry_run=False)
        
        self.assertFalse(result.success)
        self.assertIn("Could not generate command", result.error)
    
    @patch('nlcli.engine.plan_and_generate')
    def test_execute_command_dry_run(self, mock_plan):
        """Test command execution in dry run mode."""
        mock_intent = Mock(spec=Intent)
        mock_intent.command = "ls -la"
        mock_plan.return_value = mock_intent
        
        command = BatchCommand("list files")
        result = self.executor._execute_command(command, dry_run=True)
        
        self.assertTrue(result.success)
        self.assertIn("[DRY RUN]", result.output)
        self.assertIn("ls -la", result.output)


class TestBatchModeManager(unittest.TestCase):
    """Test batch mode manager."""
    
    def setUp(self):
        self.session_context = Mock(spec=SessionContext)
        self.tool_registry = Mock(spec=ToolRegistry)
        self.llm = Mock()
        self.manager = BatchModeManager(self.session_context, self.tool_registry, self.llm)
    
    def test_execute_commands_simple(self):
        """Test executing simple command list."""
        commands = ["find files", "list directory"]
        
        with patch.object(self.manager, 'execute_script_file') as mock_execute:
            mock_execute.return_value = [
                BatchResult(BatchCommand("find files"), success=True),
                BatchResult(BatchCommand("list directory"), success=True)
            ]
            
            # Execute commands list (this internally creates a BatchScript)
            with patch.object(BatchExecutor, 'execute_script') as mock_executor:
                mock_executor.return_value = [
                    BatchResult(BatchCommand("find files"), success=True),
                    BatchResult(BatchCommand("list directory"), success=True)
                ]
                
                results = self.manager.execute_commands(commands)
                
                self.assertEqual(len(results), 2)
                self.assertTrue(all(r.success for r in results))
    
    def test_create_example_script(self):
        """Test creating example script."""
        example = self.manager.create_example_script()
        
        self.assertIn("@name", example)
        self.assertIn("@description", example)
        self.assertIn("BASE_DIR=", example)
        self.assertIn("> find", example)
        self.assertIn("depends:", example)
    
    def test_validate_script_valid(self):
        """Test validating a valid script."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.nlcli', delete=False) as f:
            f.write("""> command 1
> command 2
depends: 1
> command 3
""")
            temp_path = Path(f.name)
        
        try:
            result = self.manager.validate_script(temp_path)
            
            self.assertTrue(result["valid"])
            self.assertEqual(result["commands_count"], 3)
            self.assertEqual(len(result["errors"]), 0)
        finally:
            temp_path.unlink()
    
    def test_validate_script_with_errors(self):
        """Test validating script with errors."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.nlcli', delete=False) as f:
            f.write("""> command 1
depends: 1
""")  # Self-dependency error
            temp_path = Path(f.name)
        
        try:
            result = self.manager.validate_script(temp_path)
            
            self.assertFalse(result["valid"])
            self.assertGreater(len(result["errors"]), 0)
            self.assertIn("depends on itself", result["errors"][0])
        finally:
            temp_path.unlink()
    
    def test_format_results(self):
        """Test formatting batch results."""
        results = [
            BatchResult(
                command=BatchCommand("find files", generated_command="find . -name '*.txt'"),
                success=True,
                output="file1.txt\nfile2.txt",
                duration=1.2
            ),
            BatchResult(
                command=BatchCommand("invalid command"),
                success=False,
                error="Command not found",
                duration=0.1
            ),
            BatchResult(
                command=BatchCommand("skipped command"),
                success=True,
                skipped=True,
                skip_reason="Condition not met",
                duration=0.0
            )
        ]
        
        formatted = self.manager.format_results(results)
        
        self.assertIn("Batch Execution Results", formatted)
        self.assertIn("Success: 1", formatted)
        self.assertIn("Failed: 1", formatted)
        self.assertIn("Skipped: 1", formatted)
        self.assertIn("find files", formatted)
        self.assertIn("Duration: 1.20s", formatted)
    
    def test_format_empty_results(self):
        """Test formatting empty results."""
        formatted = self.manager.format_results([])
        self.assertEqual(formatted, "No commands executed.")


if __name__ == '__main__':
    unittest.main()