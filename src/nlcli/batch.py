"""
Scripting and Batch Mode
Support for executing commands in batch mode and script files.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class BatchCommand:
    """Represents a command in a batch script."""

    natural_language: str
    generated_command: Optional[str] = None
    line_number: int = 0
    depends_on: List[int] = field(default_factory=list)
    condition: Optional[str] = None  # success, failure, always
    timeout: Optional[int] = None
    retry_count: int = 0
    variables: Dict[str, str] = field(default_factory=dict)


@dataclass
class BatchResult:
    """Result of executing a batch command."""

    command: BatchCommand
    success: bool
    output: str = ""
    error: str = ""
    exit_code: int = 0
    duration: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    skipped: bool = False
    skip_reason: str = ""


@dataclass
class BatchScript:
    """Represents a complete batch script."""

    commands: List[BatchCommand]
    variables: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    script_path: Optional[Path] = None


class BatchScriptParser:
    """Parser for batch script files."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def parse_file(self, script_path: Path) -> BatchScript:
        """Parse a batch script file."""
        if not script_path.exists():
            raise FileNotFoundError(f"Script file not found: {script_path}")

        content = script_path.read_text(encoding="utf-8")
        return self.parse_content(content, script_path)

    def parse_content(
        self, content: str, script_path: Optional[Path] = None
    ) -> BatchScript:
        """Parse batch script content."""
        lines = content.split("\n")
        commands = []
        variables = {}
        metadata = {}
        current_line = 0

        for line in lines:
            current_line += 1
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Parse metadata (starts with @)
            if line.startswith("@"):
                self._parse_metadata_line(line, metadata)
                continue

            # Parse variable assignments (but not command modifiers)
            if "=" in line and not line.startswith(">") and not line.startswith("var:"):
                self._parse_variable_line(line, variables)
                continue

            # Parse commands (natural language starting with >)
            if line.startswith(">"):
                command = self._parse_command_line(line, current_line)
                commands.append(command)
                continue

            # Parse command modifiers (depends, condition, etc.)
            if commands:  # Apply to last command
                self._parse_modifier_line(line, commands[-1])

        return BatchScript(
            commands=commands,
            variables=variables,
            metadata=metadata,
            script_path=script_path,
        )

    def _parse_metadata_line(self, line: str, metadata: Dict[str, Any]) -> None:
        """Parse metadata line (@key value)."""
        parts = line[1:].split(" ", 1)
        if len(parts) == 2:
            key, value = parts
            metadata[key.strip()] = value.strip()

    def _parse_variable_line(self, line: str, variables: Dict[str, str]) -> None:
        """Parse variable assignment (key=value)."""
        parts = line.split("=", 1)
        if len(parts) == 2:
            key, value = parts
            variables[key.strip()] = value.strip()

    def _parse_command_line(self, line: str, line_number: int) -> BatchCommand:
        """Parse command line (> natural language command)."""
        nl_command = line[1:].strip()
        return BatchCommand(natural_language=nl_command, line_number=line_number)

    def _parse_modifier_line(self, line: str, command: BatchCommand) -> None:
        """Parse command modifier line."""
        if line.startswith("depends:"):
            # Parse dependencies
            deps_str = line[8:].strip()
            deps = [int(d.strip()) for d in deps_str.split(",") if d.strip().isdigit()]
            command.depends_on.extend(deps)

        elif line.startswith("condition:"):
            # Parse execution condition
            command.condition = line[10:].strip()

        elif line.startswith("timeout:"):
            # Parse timeout
            timeout_str = line[8:].strip()
            if timeout_str.isdigit():
                command.timeout = int(timeout_str)

        elif line.startswith("retry:"):
            # Parse retry count
            retry_str = line[6:].strip()
            if retry_str.isdigit():
                command.retry_count = int(retry_str)

        elif line.startswith("var:"):
            # Parse command-specific variables
            var_line = line[4:].strip()
            if "=" in var_line:
                key, value = var_line.split("=", 1)
                command.variables[key.strip()] = value.strip()


class BatchExecutor:
    """Executes batch scripts with dependency management and error handling."""

    def __init__(self, session_context, tool_registry, llm=None):
        self.session_context = session_context
        self.tool_registry = tool_registry
        self.llm = llm
        self.logger = logging.getLogger(__name__)
        self.results: List[BatchResult] = []
        self.variables: Dict[str, str] = {}

    def execute_script(
        self,
        script: BatchScript,
        dry_run: bool = False,
        stop_on_error: bool = True,
        max_parallel: int = 1,
    ) -> List[BatchResult]:
        """Execute a batch script."""
        self.logger.info(
            f"Starting batch execution with {len(script.commands)} commands"
        )

        # Initialize variables
        self.variables = script.variables.copy()
        self.results = []

        # Build execution plan
        execution_order = self._build_execution_order(script.commands)

        if max_parallel == 1:
            # Sequential execution
            return self._execute_sequential(execution_order, dry_run, stop_on_error)
        else:
            # Parallel execution (simplified for now)
            return self._execute_sequential(execution_order, dry_run, stop_on_error)

    def _build_execution_order(
        self, commands: List[BatchCommand]
    ) -> List[List[BatchCommand]]:
        """Build execution order respecting dependencies."""
        # For now, simple approach: respect line order and basic dependencies
        # In a full implementation, this would use topological sorting

        execution_groups = []
        remaining_commands = commands.copy()

        while remaining_commands:
            # Find commands with no unmet dependencies
            ready_commands = []
            for cmd in remaining_commands:
                if self._dependencies_satisfied(cmd, execution_groups):
                    ready_commands.append(cmd)

            if not ready_commands:
                # Circular dependency or other issue, just take the first
                ready_commands = [remaining_commands[0]]
                self.logger.warning("Possible circular dependency detected")

            execution_groups.append(ready_commands)
            for cmd in ready_commands:
                remaining_commands.remove(cmd)

        return execution_groups

    def _dependencies_satisfied(
        self, command: BatchCommand, completed_groups: List[List[BatchCommand]]
    ) -> bool:
        """Check if command dependencies are satisfied."""
        if not command.depends_on:
            return True

        completed_lines = set()
        for group in completed_groups:
            for cmd in group:
                completed_lines.add(cmd.line_number)

        return all(dep in completed_lines for dep in command.depends_on)

    def _execute_sequential(
        self,
        execution_groups: List[List[BatchCommand]],
        dry_run: bool,
        stop_on_error: bool,
    ) -> List[BatchResult]:
        """Execute commands sequentially."""

        for group in execution_groups:
            for command in group:
                # Check execution condition
                if not self._should_execute(command):
                    result = BatchResult(
                        command=command,
                        success=True,
                        skipped=True,
                        skip_reason=f"Condition not met: {command.condition}",
                    )
                    self.results.append(result)
                    continue

                # Substitute variables
                processed_command = self._substitute_variables(command)

                # Execute command
                result = self._execute_command(processed_command, dry_run)
                self.results.append(result)

                # Handle retry
                if not result.success and command.retry_count > 0:
                    for retry in range(command.retry_count):
                        self.logger.info(
                            f"Retrying command (attempt {retry + 1}/"
                            f"{command.retry_count})"
                        )
                        time.sleep(1)  # Wait before retry

                        retry_result = self._execute_command(processed_command, dry_run)
                        if retry_result.success:
                            result = retry_result
                            break

                # Check if we should stop on error
                if stop_on_error and not result.success:
                    self.logger.error(
                        f"Stopping execution due to error: {result.error}"
                    )
                    break

        return self.results

    def _should_execute(self, command: BatchCommand) -> bool:
        """Determine if command should be executed based on condition."""
        if not command.condition:
            return True

        condition = command.condition.lower()

        if condition == "always":
            return True
        elif condition == "success":
            # Execute only if previous command succeeded
            return not self.results or self.results[-1].success
        elif condition == "failure":
            # Execute only if previous command failed
            return self.results and not self.results[-1].success

        return True

    def _substitute_variables(self, command: BatchCommand) -> BatchCommand:
        """Substitute variables in command."""
        processed_nl = command.natural_language

        # Combine global and command-specific variables
        all_variables = self.variables.copy()
        all_variables.update(command.variables)

        # Simple variable substitution
        for var_name, var_value in all_variables.items():
            processed_nl = processed_nl.replace(f"${var_name}", var_value)
            processed_nl = processed_nl.replace(f"${{{var_name}}}", var_value)

        # Create new command with substituted text
        new_command = BatchCommand(
            natural_language=processed_nl,
            generated_command=command.generated_command,
            line_number=command.line_number,
            depends_on=command.depends_on,
            condition=command.condition,
            timeout=command.timeout,
            retry_count=command.retry_count,
            variables=command.variables,
        )

        return new_command

    def _execute_command(self, command: BatchCommand, dry_run: bool) -> BatchResult:
        """Execute a single command."""
        start_time = time.time()

        try:
            # Generate command from natural language
            from nlcli.engine import plan_and_generate

            intent = plan_and_generate(
                command.natural_language,
                self.session_context,
                self.tool_registry,
                self.llm,
            )

            if not intent:
                return BatchResult(
                    command=command,
                    success=False,
                    error="Could not generate command from natural language",
                    duration=time.time() - start_time,
                )

            command.generated_command = intent.command

            if dry_run:
                return BatchResult(
                    command=command,
                    success=True,
                    output=f"[DRY RUN] Would execute: {intent.command}",
                    duration=time.time() - start_time,
                )

            # Execute the command
            from nlcli.executor import execute

            execution_result = execute(intent.command, self.session_context)

            # Update variables from output if needed
            self._update_variables_from_output(execution_result.output)

            return BatchResult(
                command=command,
                success=execution_result.success,
                output=execution_result.output,
                error=execution_result.error,
                exit_code=execution_result.exit_code,
                duration=time.time() - start_time,
            )

        except Exception as e:
            self.logger.error(f"Error executing command: {e}")
            return BatchResult(
                command=command,
                success=False,
                error=str(e),
                duration=time.time() - start_time,
            )

    def _update_variables_from_output(self, output: str) -> None:
        """Update variables from command output (basic implementation)."""
        # This could parse command output to extract values
        # For now, just store the last output
        self.variables["LAST_OUTPUT"] = output.strip() if output else ""


class BatchModeManager:
    """Manager for batch mode operations."""

    def __init__(self, session_context, tool_registry, llm=None):
        self.session_context = session_context
        self.tool_registry = tool_registry
        self.llm = llm
        self.parser = BatchScriptParser()
        self.logger = logging.getLogger(__name__)

    def execute_script_file(self, script_path: Path, **kwargs) -> List[BatchResult]:
        """Execute a batch script file."""
        script = self.parser.parse_file(script_path)
        executor = BatchExecutor(self.session_context, self.tool_registry, self.llm)
        return executor.execute_script(script, **kwargs)

    def execute_commands(self, commands: List[str], **kwargs) -> List[BatchResult]:
        """Execute a list of natural language commands."""
        batch_commands = []
        for i, nl_command in enumerate(commands, 1):
            batch_commands.append(
                BatchCommand(natural_language=nl_command, line_number=i)
            )

        script = BatchScript(commands=batch_commands)
        executor = BatchExecutor(self.session_context, self.tool_registry, self.llm)
        return executor.execute_script(script, **kwargs)

    def create_example_script(self) -> str:
        """Create an example batch script."""
        return """# Example NLCLI Batch Script
@name Example File Management Script
@description Demonstrate batch operations on files
@version 1.0

# Variables
BASE_DIR=/tmp/test
LOG_FILE=/tmp/nlcli_batch.log

# Commands
> find all .txt files larger than 1MB
condition: always
timeout: 30

> list files in ${BASE_DIR}
depends: 2
condition: success

> create directory called backup in ${BASE_DIR}
depends: 3
retry: 2

> copy large files to backup directory
depends: 4
condition: success
timeout: 60
"""

    def validate_script(self, script_path: Path) -> Dict[str, Any]:
        """Validate a batch script."""
        try:
            script = self.parser.parse_file(script_path)

            validation_result = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "commands_count": len(script.commands),
                "variables_count": len(script.variables),
            }

            # Check for circular dependencies
            for cmd in script.commands:
                if cmd.line_number in cmd.depends_on:
                    validation_result["errors"].append(
                        f"Command at line {cmd.line_number} depends on itself"
                    )

            # Check dependency references
            line_numbers = {cmd.line_number for cmd in script.commands}
            for cmd in script.commands:
                for dep in cmd.depends_on:
                    if dep not in line_numbers:
                        validation_result["warnings"].append(
                            f"Command at line {cmd.line_number} depends on "
                            f"non-existent line {dep}"
                        )

            if validation_result["errors"]:
                validation_result["valid"] = False

            return validation_result

        except Exception as e:
            return {
                "valid": False,
                "errors": [str(e)],
                "warnings": [],
                "commands_count": 0,
                "variables_count": 0,
            }

    def format_results(self, results: List[BatchResult]) -> str:
        """Format batch execution results."""
        if not results:
            return "No commands executed."

        output_lines = []
        output_lines.append(f"Batch Execution Results ({len(results)} commands)")
        output_lines.append("=" * 50)

        successful = sum(1 for r in results if r.success and not r.skipped)
        failed = sum(1 for r in results if not r.success and not r.skipped)
        skipped = sum(1 for r in results if r.skipped)

        output_lines.append(f"[OK] Success: {successful}")
        output_lines.append(f"[FAIL] Failed: {failed}")
        output_lines.append(f"[SKIP] Skipped: {skipped}")
        output_lines.append("")

        for i, result in enumerate(results, 1):
            status = "[OK]" if result.success else "[FAIL]"
            if result.skipped:
                status = "[SKIP]"

            output_lines.append(
                f"{status} Command {i}: {result.command.natural_language}"
            )

            if result.command.generated_command:
                output_lines.append(f"   Generated: {result.command.generated_command}")

            if result.output and not result.skipped:
                output_lines.append(f"   Output: {result.output[:100]}...")

            if result.error:
                output_lines.append(f"   Error: {result.error}")

            output_lines.append(f"   Duration: {result.duration:.2f}s")
            output_lines.append("")

        return "\n".join(output_lines)


# Global batch mode manager instance
_batch_manager: Optional[BatchModeManager] = None


def get_batch_manager(
    session_context=None, tool_registry=None, llm=None
) -> Optional[BatchModeManager]:
    """Get batch mode manager instance."""
    global _batch_manager
    if _batch_manager is None and session_context and tool_registry:
        _batch_manager = BatchModeManager(session_context, tool_registry, llm)
    return _batch_manager
