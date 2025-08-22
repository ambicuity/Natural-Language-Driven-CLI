"""
Advanced Error Recovery Module.
Implements robust error handling, retry mechanisms, and graceful degradation.
"""

import logging
import random
import time
import traceback
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple


class ErrorSeverity(Enum):
    """Error severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""

    NETWORK = "network"
    FILESYSTEM = "filesystem"
    PERMISSION = "permission"
    RESOURCE = "resource"
    PARSING = "parsing"
    VALIDATION = "validation"
    EXTERNAL_TOOL = "external_tool"
    LLM = "llm"
    PLUGIN = "plugin"
    SYSTEM = "system"
    USER_INPUT = "user_input"
    CONFIGURATION = "configuration"


@dataclass
class ErrorContext:
    """Context information for errors."""

    operation: str
    command: Optional[str] = None
    user_input: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class RecoveryAction:
    """Action to take for error recovery."""

    action_type: str
    description: str
    auto_apply: bool = False
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorRecord:
    """Record of an error and recovery attempt."""

    error_type: str
    error_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    context: ErrorContext
    traceback: Optional[str]
    recovery_attempts: List[RecoveryAction] = field(default_factory=list)
    resolved: bool = False
    timestamp: float = field(default_factory=time.time)


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""
        delay = self.base_delay * (self.exponential_base ** (attempt - 1))
        delay = min(delay, self.max_delay)

        if self.jitter:
            # Add random jitter (±25%)
            jitter_amount = delay * 0.25
            delay += random.uniform(-jitter_amount, jitter_amount)

        return max(0, delay)


class ErrorClassifier:
    """Classifies errors and determines recovery strategies."""

    def __init__(self):
        self.error_patterns = {
            # Network errors
            ErrorCategory.NETWORK: [
                ("connection refused", ErrorSeverity.HIGH),
                ("timeout", ErrorSeverity.MEDIUM),
                ("dns resolution failed", ErrorSeverity.MEDIUM),
                ("no route to host", ErrorSeverity.HIGH),
                ("network unreachable", ErrorSeverity.HIGH),
            ],
            # Filesystem errors
            ErrorCategory.FILESYSTEM: [
                ("no such file or directory", ErrorSeverity.MEDIUM),
                ("permission denied", ErrorSeverity.HIGH),
                ("disk full", ErrorSeverity.CRITICAL),
                ("directory not empty", ErrorSeverity.MEDIUM),
                ("file exists", ErrorSeverity.LOW),
            ],
            # Permission errors
            ErrorCategory.PERMISSION: [
                ("access denied", ErrorSeverity.HIGH),
                ("operation not permitted", ErrorSeverity.HIGH),
                ("insufficient privileges", ErrorSeverity.HIGH),
                ("authentication failed", ErrorSeverity.CRITICAL),
            ],
            # Resource errors
            ErrorCategory.RESOURCE: [
                ("out of memory", ErrorSeverity.CRITICAL),
                ("resource temporarily unavailable", ErrorSeverity.MEDIUM),
                ("too many open files", ErrorSeverity.HIGH),
                ("process limit exceeded", ErrorSeverity.HIGH),
            ],
            # External tool errors
            ErrorCategory.EXTERNAL_TOOL: [
                ("command not found", ErrorSeverity.HIGH),
                ("tool not installed", ErrorSeverity.HIGH),
                ("invalid option", ErrorSeverity.MEDIUM),
                ("syntax error", ErrorSeverity.MEDIUM),
            ],
        }

        self.recovery_strategies = {
            ErrorCategory.NETWORK: [
                RecoveryAction(
                    "retry_with_backoff", "Retry with exponential backoff", True
                ),
                RecoveryAction(
                    "use_alternative_endpoint",
                    "Try alternative network endpoint",
                    False,
                ),
                RecoveryAction("enable_offline_mode", "Switch to offline mode", True),
            ],
            ErrorCategory.FILESYSTEM: [
                RecoveryAction("create_directory", "Create missing directory", True),
                RecoveryAction("use_temp_location", "Use temporary location", True),
                RecoveryAction("cleanup_space", "Clean up disk space", False),
            ],
            ErrorCategory.PERMISSION: [
                RecoveryAction(
                    "suggest_sudo", "Suggest using elevated permissions", False
                ),
                RecoveryAction(
                    "use_user_directory", "Use user-accessible directory", True
                ),
                RecoveryAction("change_permissions", "Modify file permissions", False),
            ],
            ErrorCategory.RESOURCE: [
                RecoveryAction(
                    "reduce_concurrency", "Reduce concurrent operations", True
                ),
                RecoveryAction("cleanup_resources", "Clean up unused resources", True),
                RecoveryAction("use_streaming", "Use streaming processing", True),
            ],
            ErrorCategory.EXTERNAL_TOOL: [
                RecoveryAction(
                    "suggest_installation", "Suggest installing missing tool", False
                ),
                RecoveryAction("use_alternative_tool", "Use alternative tool", True),
                RecoveryAction("provide_manual_steps", "Provide manual steps", False),
            ],
            ErrorCategory.LLM: [
                RecoveryAction("fallback_to_cloud", "Fallback to cloud LLM", True),
                RecoveryAction("use_heuristics", "Use rule-based parsing", True),
                RecoveryAction(
                    "request_clarification", "Request user clarification", False
                ),
            ],
        }

    def classify_error(
        self, error: Exception, context: ErrorContext
    ) -> Tuple[ErrorCategory, ErrorSeverity]:
        """Classify an error and determine its severity."""
        error_message = str(error).lower()
        _error_type = type(error).__name__  # noqa: F841

        # Check error patterns
        for category, patterns in self.error_patterns.items():
            for pattern, severity in patterns:
                if pattern in error_message:
                    return category, severity

        # Classify by exception type
        if isinstance(error, (ConnectionError, TimeoutError)):
            return ErrorCategory.NETWORK, ErrorSeverity.HIGH
        elif isinstance(error, (FileNotFoundError, OSError, IOError)):
            return ErrorCategory.FILESYSTEM, ErrorSeverity.MEDIUM
        elif isinstance(error, PermissionError):
            return ErrorCategory.PERMISSION, ErrorSeverity.HIGH
        elif isinstance(error, MemoryError):
            return ErrorCategory.RESOURCE, ErrorSeverity.CRITICAL
        elif isinstance(error, (ValueError, TypeError)):
            return ErrorCategory.PARSING, ErrorSeverity.MEDIUM

        # Default classification
        return ErrorCategory.SYSTEM, ErrorSeverity.MEDIUM

    def get_recovery_actions(self, category: ErrorCategory) -> List[RecoveryAction]:
        """Get recovery actions for error category."""
        return self.recovery_strategies.get(category, [])


class ErrorRecoveryManager:
    """Manages error recovery across the application."""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ErrorRecoveryManager")
        self.classifier = ErrorClassifier()
        self.error_history: List[ErrorRecord] = []
        self.recovery_handlers: Dict[ErrorCategory, List[Callable]] = {}

        # Default retry configurations
        self.retry_configs = {
            ErrorCategory.NETWORK: RetryConfig(max_attempts=3, base_delay=1.0),
            ErrorCategory.FILESYSTEM: RetryConfig(max_attempts=2, base_delay=0.5),
            ErrorCategory.LLM: RetryConfig(max_attempts=2, base_delay=2.0),
            ErrorCategory.EXTERNAL_TOOL: RetryConfig(max_attempts=1, base_delay=0.1),
        }

    def register_recovery_handler(self, category: ErrorCategory, handler: Callable):
        """Register a custom recovery handler for an error category."""
        if category not in self.recovery_handlers:
            self.recovery_handlers[category] = []
        self.recovery_handlers[category].append(handler)

    def handle_error(
        self, error: Exception, context: ErrorContext, allow_recovery: bool = True
    ) -> Optional[Any]:
        """
        Handle an error with automatic recovery attempts.

        Args:
            error: The exception that occurred
            context: Context information
            allow_recovery: Whether to attempt recovery

        Returns:
            Recovery result if successful, None otherwise
        """
        # Classify error
        category, severity = self.classifier.classify_error(error, context)

        # Create error record
        error_record = ErrorRecord(
            error_type=type(error).__name__,
            error_message=str(error),
            severity=severity,
            category=category,
            context=context,
            traceback=traceback.format_exc(),
        )

        self.error_history.append(error_record)

        # Log error
        self.logger.error(
            f"Error in {context.operation}: {error} (Category: {category.value}, Severity: {severity.value})"
        )

        if not allow_recovery:
            return None

        # Attempt recovery
        recovery_result = self._attempt_recovery(error_record)

        if recovery_result:
            error_record.resolved = True
            self.logger.info(
                f"Successfully recovered from error in {context.operation}"
            )

        return recovery_result

    def _attempt_recovery(self, error_record: ErrorRecord) -> Optional[Any]:
        """Attempt to recover from an error."""
        category = error_record.category

        # Get recovery actions
        recovery_actions = self.classifier.get_recovery_actions(category)

        # Execute custom handlers first
        if category in self.recovery_handlers:
            for handler in self.recovery_handlers[category]:
                try:
                    result = handler(error_record)
                    if result:
                        return result
                except Exception as e:
                    self.logger.warning(f"Recovery handler failed: {e}")

        # Execute built-in recovery actions
        for action in recovery_actions:
            if action.auto_apply:
                try:
                    result = self._execute_recovery_action(action, error_record)
                    if result:
                        error_record.recovery_attempts.append(action)
                        return result
                except Exception as e:
                    self.logger.warning(
                        f"Recovery action '{action.action_type}' failed: {e}"
                    )

        return None

    def _execute_recovery_action(
        self, action: RecoveryAction, error_record: ErrorRecord
    ) -> Optional[Any]:
        """Execute a specific recovery action."""
        if action.action_type == "retry_with_backoff":
            # This would be handled by the retry decorator
            return True
        elif action.action_type == "use_temp_location":
            # Switch to temporary directory
            import tempfile

            temp_dir = tempfile.mkdtemp()
            return {"temp_directory": temp_dir}
        elif action.action_type == "reduce_concurrency":
            # Signal to reduce concurrent operations
            return {"reduce_concurrency": True}
        elif action.action_type == "cleanup_resources":
            # Trigger resource cleanup
            import gc

            gc.collect()
            return True
        elif action.action_type == "use_heuristics":
            # Fallback to non-LLM processing
            return {"use_fallback": True}

        return None

    def get_error_patterns(self, hours: int = 24) -> Dict[str, Any]:
        """Analyze error patterns from recent history."""
        cutoff_time = time.time() - (hours * 3600)
        recent_errors = [
            error for error in self.error_history if error.timestamp >= cutoff_time
        ]

        if not recent_errors:
            return {"total_errors": 0, "period_hours": hours}

        # Analyze patterns
        by_category = {}
        by_severity = {}
        by_operation = {}
        resolution_rate = 0

        for error in recent_errors:
            category = error.category.value
            severity = error.severity.value
            operation = error.context.operation

            by_category[category] = by_category.get(category, 0) + 1
            by_severity[severity] = by_severity.get(severity, 0) + 1
            by_operation[operation] = by_operation.get(operation, 0) + 1

            if error.resolved:
                resolution_rate += 1

        resolution_rate = resolution_rate / len(recent_errors)

        return {
            "total_errors": len(recent_errors),
            "period_hours": hours,
            "resolution_rate": resolution_rate,
            "by_category": by_category,
            "by_severity": by_severity,
            "by_operation": by_operation,
            "most_common_category": (
                max(by_category.items(), key=lambda x: x[1])[0] if by_category else None
            ),
            "most_problematic_operation": (
                max(by_operation.items(), key=lambda x: x[1])[0]
                if by_operation
                else None
            ),
        }


def with_retry(
    category: Optional[ErrorCategory] = None,
    retry_config: Optional[RetryConfig] = None,
    error_context: Optional[ErrorContext] = None,
):
    """Decorator for automatic retry with exponential backoff."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get or create retry config
            config = retry_config
            if config is None and category:
                manager = get_error_recovery_manager()
                config = manager.retry_configs.get(category, RetryConfig())
            elif config is None:
                config = RetryConfig()

            last_exception = None

            for attempt in range(1, config.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if attempt < config.max_attempts:
                        delay = config.get_delay(attempt)
                        logging.getLogger(func.__module__).warning(
                            f"Attempt {attempt}/{config.max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logging.getLogger(func.__module__).error(
                            f"All {config.max_attempts} attempts failed for {func.__name__}: {e}"
                        )

            # If we get here, all attempts failed
            if error_context and last_exception:
                manager = get_error_recovery_manager()
                manager.handle_error(last_exception, error_context)

            raise last_exception

        return wrapper

    return decorator


def graceful_fallback(fallback_value: Any = None, log_error: bool = True):
    """Decorator for graceful fallback on errors."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logging.getLogger(func.__module__).warning(
                        f"Function {func.__name__} failed with {e}, using fallback value"
                    )
                return fallback_value

        return wrapper

    return decorator


# Global error recovery manager
_error_recovery_manager: Optional[ErrorRecoveryManager] = None


def get_error_recovery_manager() -> ErrorRecoveryManager:
    """Get global error recovery manager instance."""
    global _error_recovery_manager
    if _error_recovery_manager is None:
        _error_recovery_manager = ErrorRecoveryManager()
    return _error_recovery_manager
