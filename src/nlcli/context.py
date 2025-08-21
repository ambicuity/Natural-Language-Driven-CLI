"""
Session Context Management
Handles ephemeral session state and durable preferences.
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table
from rich.text import Text


@dataclass
class ExecutionResult:
    """Result of command execution."""

    success: bool
    output: str = ""
    error: str = ""
    exit_code: int = 0
    duration_ms: float = 0.0


@dataclass
class Intent:
    """Structured representation of user intent."""

    tool_name: str
    args: Dict[str, Any]
    command: str
    explanation: str
    danger_level: str = "read_only"  # read_only, modify, destructive
    confidence: float = 1.0


class SessionContext:
    """
    Manages session state including current directory, active filters,
    recent results, and user preferences.
    """

    def __init__(self):
        self.cwd = Path.cwd()
        self.filters: Dict[str, Any] = {}
        self.recent_files: List[str] = []
        self.recent_processes: List[Dict[str, Any]] = []
        self.command_history: List[Intent] = []
        self.start_time = datetime.now()

        # User preferences (would be loaded from config file)
        self.preferences = {
            "default_editor": os.environ.get("EDITOR", "nano"),
            "confirm_by_default": True,
            "allowed_directories": [str(Path.home())],
            "model_preference": "local",
            "language": os.environ.get("NLCLI_DEFAULT_LANG", "en"),
            "max_results": 50,
            "trash_instead_of_delete": True,
            "auto_detect_language": os.environ.get(
                "NLCLI_AUTO_DETECT_LANG", "true"
            ).lower()
            == "true",
        }

    def clear(self) -> None:
        """Clear ephemeral session state."""
        self.filters.clear()
        self.recent_files.clear()
        self.recent_processes.clear()
        # Keep command history for reference

    def update_cwd(self, new_path: Path) -> None:
        """Update current working directory."""
        if new_path.exists() and new_path.is_dir():
            self.cwd = new_path.resolve()

    def add_filter(self, key: str, value: Any) -> None:
        """Add a filter that persists across commands in the session."""
        self.filters[key] = value

    def remove_filter(self, key: str) -> None:
        """Remove a filter."""
        self.filters.pop(key, None)

    def update_from_intent(self, intent: Intent) -> None:
        """Update context based on executed intent."""
        self.command_history.append(intent)

        # Update filters based on intent args
        if "path" in intent.args:
            path_val = intent.args["path"]
            if path_val != "." and Path(path_val).exists():
                self.add_filter("active_path", path_val)

        if "min_size" in intent.args:
            self.add_filter("min_size", intent.args["min_size"])

        if "modified_within" in intent.args:
            self.add_filter("time_filter", intent.args["modified_within"])

    def update_from_result(self, result: ExecutionResult) -> None:
        """Update context based on execution result."""
        if result.success and result.output:
            # Parse output for file paths and store recent results
            lines = result.output.strip().split("\n")
            for line in lines:
                if line and Path(line.strip()).exists():
                    if line not in self.recent_files:
                        self.recent_files.append(line.strip())
                        # Keep only most recent files
                        if len(self.recent_files) > self.preferences["max_results"]:
                            self.recent_files.pop(0)

    def get_recent_files(self, limit: Optional[int] = None) -> List[str]:
        """Get recently accessed files."""
        if limit:
            return self.recent_files[-limit:]
        return self.recent_files

    def resolve_pronouns(self, text: str) -> str:
        """Resolve pronouns like 'those', 'them', 'same' to recent context."""
        # First process multi-language input
        try:
            from nlcli.language import get_language_processor

            lang_processor = get_language_processor()

            user_lang = self.preferences.get("language", "en")
            auto_detect = self.preferences.get("auto_detect_language", True)

            if auto_detect:
                lang_result = lang_processor.process_input(text)
                if lang_result["needs_translation"]:
                    text = lang_result["translated_text"]
                    # Store detected language for future use
                    if lang_result["confidence"] > 0.5:
                        self.preferences["language"] = lang_result["detected_language"]
            elif user_lang != "en":
                lang_result = lang_processor.process_input(text, user_lang)
                if lang_result["needs_translation"]:
                    text = lang_result["translated_text"]
        except ImportError:
            # Language support not available
            pass

        pronouns = {
            "those": self.recent_files[-5:] if self.recent_files else [],
            "them": self.recent_files[-5:] if self.recent_files else [],
            "these": self.recent_files[-3:] if self.recent_files else [],
            "same": self.filters.copy(),
        }

        # Simple pronoun replacement (would be more sophisticated in practice)
        for pronoun, replacement in pronouns.items():
            if pronoun in text.lower():
                if isinstance(replacement, list) and replacement:
                    # Replace with file paths
                    text = text.replace(pronoun, " ".join(replacement[:3]))
                elif isinstance(replacement, dict) and replacement:
                    # Use active filters
                    if "active_path" in replacement:
                        text = text.replace(pronoun, f"in {replacement['active_path']}")

        return text

    def get_context_for_command(self) -> Dict[str, Any]:
        """Get context information for command generation."""
        return {
            "cwd": str(self.cwd),
            "filters": self.filters.copy(),
            "recent_files": self.recent_files[-10:],  # Last 10 files
            "session_duration": (datetime.now() - self.start_time).total_seconds(),
            "command_count": len(self.command_history),
        }

    def is_path_allowed(self, path: Path) -> bool:
        """Check if path is within allowed directories."""
        path_str = str(path.resolve())
        for allowed_dir in self.preferences["allowed_directories"]:
            if path_str.startswith(allowed_dir):
                return True
        return False

    def get_trash_path(self) -> Path:
        """Get trash directory path."""
        trash_dir = Path.home() / ".nlcli_trash"
        trash_dir.mkdir(exist_ok=True)
        return trash_dir

    def print_context(self, console: Console) -> None:
        """Print current context information."""
        table = Table(title="Session Context", border_style="blue")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Current Directory", str(self.cwd))
        table.add_row(
            "Session Duration",
            f"{(datetime.now() - self.start_time).total_seconds():.1f}s",
        )
        table.add_row("Commands Executed", str(len(self.command_history)))

        if self.filters:
            filters_text = ", ".join(f"{k}={v}" for k, v in self.filters.items())
            table.add_row("Active Filters", filters_text)

        if self.recent_files:
            recent_text = f"{len(self.recent_files)} files (showing last 3)"
            table.add_row("Recent Files", recent_text)
            for i, file_path in enumerate(self.recent_files[-3:]):
                table.add_row("", f"  {i+1}. {file_path}")

        console.print(table)
