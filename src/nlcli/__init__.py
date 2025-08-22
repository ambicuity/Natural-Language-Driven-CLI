"""
Natural Language Driven CLI

A cross-platform command-line companion that turns natural language
("show files >1GB modified this week") into safe, auditable system commands,
with dry-runs, confirmations, and a plugin ecosystem.
"""

__version__ = "0.1.3"
__author__ = "Natural Language CLI Team"
__description__ = "Turn natural language into safe system commands"

from nlcli.context import ExecutionResult, Intent, SessionContext
from nlcli.engine import explain, plan_and_generate
from nlcli.executor import dry_run, execute
from nlcli.main import main
from nlcli.registry import ToolArg, ToolRegistry, ToolSchema
from nlcli.safety import get_undo_hint, guard, requires_confirmation

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

# Phase 3 Advanced Features
try:
    from nlcli.advanced_context import (  # noqa: F401
        AdvancedContextManager,
        get_advanced_context_manager,
    )
    from nlcli.batch import (  # noqa: F401
        BatchModeManager,
        BatchScriptParser,
        get_batch_manager,
    )
    from nlcli.cloud_llm import (  # noqa: F401
        CloudLLMService,
        get_cloud_llm_service,
    )
    from nlcli.language import (  # noqa: F401
        MultiLanguageProcessor,
        get_language_processor,
    )
    from nlcli.plugins import (  # noqa: F401
        PluginManager,
        get_plugin_manager,
    )

    __all__.extend(
        [
            "PluginManager",
            "get_plugin_manager",
            "MultiLanguageProcessor",
            "get_language_processor",
            "CloudLLMService",
            "get_cloud_llm_service",
            "AdvancedContextManager",
            "get_advanced_context_manager",
            "BatchModeManager",
            "BatchScriptParser",
            "get_batch_manager",
        ]
    )
except ImportError:
    # Phase 3 features not available
    pass
