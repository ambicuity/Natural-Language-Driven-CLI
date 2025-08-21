"""
Natural Language Driven CLI

A cross-platform command-line companion that turns natural language 
("show files >1GB modified this week") into safe, auditable system commands,
with dry-runs, confirmations, and a plugin ecosystem.
"""

__version__ = "0.1.0"
__author__ = "Natural Language CLI Team"
__description__ = "Turn natural language into safe system commands"

from nlcli.main import main
from nlcli.context import SessionContext, Intent, ExecutionResult
from nlcli.registry import ToolRegistry, ToolSchema, ToolArg
from nlcli.engine import plan_and_generate, explain
from nlcli.safety import guard, requires_confirmation, get_undo_hint
from nlcli.executor import execute, dry_run

__all__ = [
    "main",
    "SessionContext", 
    "Intent",
    "ExecutionResult",
    "ToolRegistry",
    "ToolSchema", 
    "ToolArg",
    "plan_and_generate",
    "explain",
    "guard",
    "requires_confirmation", 
    "get_undo_hint",
    "execute",
    "dry_run",
]