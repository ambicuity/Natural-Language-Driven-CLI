"""
Command Executor - Safely execute commands with timeouts and resource limits.
"""

import os
import signal
import subprocess
import time
from typing import Optional

from nlcli.context import ExecutionResult, SessionContext


class CommandExecutor:
    """Executor for running system commands safely."""

    def __init__(self):
        self.timeout_seconds = 30  # Default timeout
        self.max_output_size = 1024 * 1024  # 1MB max output

    def execute(
        self, command: str, context: SessionContext, timeout: Optional[int] = None
    ) -> ExecutionResult:
        """
        Execute a command safely with timeouts and resource limits.

        Args:
            command: Shell command to execute
            context: Session context
            timeout: Optional timeout override

        Returns:
            ExecutionResult with success status, output, and metadata
        """
        start_time = time.time()

        try:
            # Prepare execution environment
            env = os.environ.copy()
            cwd = str(context.cwd)

            # Set timeout
            exec_timeout = timeout or self.timeout_seconds

            # Execute command using subprocess
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=cwd,
                env=env,
                preexec_fn=(
                    os.setsid if os.name != "nt" else None
                ),  # Process group for cleanup
            )

            try:
                stdout, stderr = process.communicate(timeout=exec_timeout)
                exit_code = process.returncode

                # Limit output size
                if len(stdout) > self.max_output_size:
                    stdout = stdout[: self.max_output_size] + "\n... (output truncated)"

                if len(stderr) > self.max_output_size:
                    stderr = (
                        stderr[: self.max_output_size]
                        + "\n... (error output truncated)"
                    )

                # Determine success
                success = exit_code == 0

                # Combine output if there's both stdout and stderr
                output = stdout
                if stderr:
                    if output:
                        output += f"\n--- stderr ---\n{stderr}"
                    else:
                        output = stderr

                duration_ms = (time.time() - start_time) * 1000

                return ExecutionResult(
                    success=success,
                    output=output,
                    error=stderr if not success else "",
                    exit_code=exit_code,
                    duration_ms=duration_ms,
                )

            except subprocess.TimeoutExpired:
                # Kill the process group
                if os.name != "nt":
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                else:
                    process.terminate()

                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill
                    if os.name != "nt":
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    else:
                        process.kill()

                duration_ms = (time.time() - start_time) * 1000

                return ExecutionResult(
                    success=False,
                    output="",
                    error=f"Command timed out after {exec_timeout} seconds",
                    exit_code=-1,
                    duration_ms=duration_ms,
                )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            return ExecutionResult(
                success=False,
                output="",
                error=f"Execution error: {str(e)}",
                exit_code=-1,
                duration_ms=duration_ms,
            )

    def dry_run(self, command: str, context: SessionContext) -> str:
        """
        Perform a dry run - show what the command would do without executing.

        Args:
            command: Command to analyze
            context: Session context

        Returns:
            Description of what the command would do
        """
        # Simple dry-run analysis based on command structure
        parts = command.split()
        if not parts:
            return "Empty command - would do nothing"

        base_cmd = parts[0]

        dry_run_explanations = {
            "find": self._dry_run_find(command, context),
            "ls": self._dry_run_ls(command, context),
            "grep": self._dry_run_grep(command, context),
            "du": self._dry_run_du(command, context),
            "stat": self._dry_run_stat(command, context),
        }

        return dry_run_explanations.get(base_cmd, f"Would execute: {command}")

    def _dry_run_find(self, command: str, context: SessionContext) -> str:
        """Dry run explanation for find command."""
        parts = command.split()

        # Extract path
        path = "current directory"
        for i, part in enumerate(parts):
            if (
                part not in ["-type", "-size", "-mtime", "-name", "-print0"]
                and not part.startswith("-")
                and i > 0
            ):
                path = part
                break

        conditions = []

        if "-size" in command:
            size_idx = parts.index("-size")
            if size_idx + 1 < len(parts):
                conditions.append(f"size {parts[size_idx + 1]}")

        if "-mtime" in command:
            mtime_idx = parts.index("-mtime")
            if mtime_idx + 1 < len(parts):
                conditions.append(f"modified within {parts[mtime_idx + 1]} days")

        if "-name" in command:
            name_idx = parts.index("-name")
            if name_idx + 1 < len(parts):
                conditions.append(f"name matching {parts[name_idx + 1]}")

        condition_str = (
            " and ".join(conditions) if conditions else "no specific conditions"
        )

        return f"Would search for files in {path} with {condition_str}"

    def _dry_run_ls(self, command: str, context: SessionContext) -> str:
        """Dry run explanation for ls command."""
        if "-l" in command:
            return "Would list files with detailed information"
        else:
            return "Would list files"

    def _dry_run_grep(self, command: str, context: SessionContext) -> str:
        """Dry run explanation for grep command."""
        # Extract pattern (first quoted string or word after flags)
        import re

        pattern_match = re.search(r"'([^']+)'|\"([^\"]+)\"|(\w+)", command)
        pattern = "specified pattern"
        if pattern_match:
            pattern = (
                pattern_match.group(1)
                or pattern_match.group(2)
                or pattern_match.group(3)
            )

        return f"Would search for '{pattern}' in files"

    def _dry_run_du(self, command: str, context: SessionContext) -> str:
        """Dry run explanation for du command."""
        return "Would show disk usage information"

    def _dry_run_stat(self, command: str, context: SessionContext) -> str:
        """Dry run explanation for stat command."""
        return "Would show file/directory information"


# Global executor instance
_executor = CommandExecutor()


def execute(
    command: str, context: SessionContext, timeout: Optional[int] = None
) -> ExecutionResult:
    """
    Execute a command.

    Args:
        command: Shell command to execute
        context: Session context
        timeout: Optional timeout in seconds

    Returns:
        ExecutionResult
    """
    return _executor.execute(command, context, timeout)


def dry_run(command: str, context: SessionContext) -> str:
    """
    Perform dry run analysis.

    Args:
        command: Command to analyze
        context: Session context

    Returns:
        Explanation of what command would do
    """
    return _executor.dry_run(command, context)
