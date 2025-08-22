"""
Telemetry and Metrics Collection Module.
Implements comprehensive observability, logging, and analytics.
"""

import json
import logging
import logging.handlers
import sys
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union


class MetricType(Enum):
    """Types of metrics that can be collected."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    EVENT = "event"


class EventType(Enum):
    """Types of events to track."""

    COMMAND_EXECUTED = "command_executed"
    COMMAND_PLANNED = "command_planned"
    LLM_QUERY = "llm_query"
    PLUGIN_LOADED = "plugin_loaded"
    ERROR_OCCURRED = "error_occurred"
    USER_SESSION_START = "user_session_start"
    USER_SESSION_END = "user_session_end"
    SECURITY_VIOLATION = "security_violation"
    PERFORMANCE_WARNING = "performance_warning"
    TOOL_MATCHED = "tool_matched"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"


@dataclass
class MetricPoint:
    """A single metric data point."""

    name: str
    value: Union[int, float]
    metric_type: MetricType
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Event:
    """An event to be logged."""

    event_type: EventType
    timestamp: float = field(default_factory=time.time)
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionInfo:
    """Information about a user session."""

    session_id: str
    start_time: float
    end_time: Optional[float] = None
    user_agent: Optional[str] = None
    commands_executed: int = 0
    errors_encountered: int = 0
    llm_queries: int = 0
    plugins_used: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """Collects and manages metrics."""

    def __init__(self, max_metrics: int = 100000):
        self.max_metrics = max_metrics
        self.metrics: deque = deque(maxlen=max_metrics)
        self._lock = threading.RLock()
        self.logger = logging.getLogger(f"{__name__}.MetricsCollector")

        # Aggregated metrics
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.timers: Dict[str, List[float]] = defaultdict(list)

    def record_metric(self, metric: MetricPoint) -> None:
        """Record a metric point."""
        with self._lock:
            self.metrics.append(metric)

            # Update aggregated metrics
            if metric.metric_type == MetricType.COUNTER:
                self.counters[metric.name] += metric.value
            elif metric.metric_type == MetricType.GAUGE:
                self.gauges[metric.name] = metric.value
            elif metric.metric_type == MetricType.HISTOGRAM:
                self.histograms[metric.name].append(metric.value)
            elif metric.metric_type == MetricType.TIMER:
                self.timers[metric.name].append(metric.value)

    def increment_counter(
        self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment a counter metric."""
        self.record_metric(
            MetricPoint(
                name=name, value=value, metric_type=MetricType.COUNTER, tags=tags or {}
            )
        )

    def set_gauge(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Set a gauge metric."""
        self.record_metric(
            MetricPoint(
                name=name, value=value, metric_type=MetricType.GAUGE, tags=tags or {}
            )
        )

    def record_histogram(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a histogram metric."""
        self.record_metric(
            MetricPoint(
                name=name,
                value=value,
                metric_type=MetricType.HISTOGRAM,
                tags=tags or {},
            )
        )

    def record_timer(
        self, name: str, duration: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a timer metric."""
        self.record_metric(
            MetricPoint(
                name=name, value=duration, metric_type=MetricType.TIMER, tags=tags or {}
            )
        )

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics."""
        with self._lock:
            summary = {
                "total_metrics": len(self.metrics),
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histograms": {},
                "timers": {},
            }

            # Calculate histogram statistics
            for name, values in self.histograms.items():
                if values:
                    summary["histograms"][name] = {
                        "count": len(values),
                        "min": min(values),
                        "max": max(values),
                        "avg": sum(values) / len(values),
                        "p95": self._percentile(values, 95),
                        "p99": self._percentile(values, 99),
                    }

            # Calculate timer statistics
            for name, durations in self.timers.items():
                if durations:
                    summary["timers"][name] = {
                        "count": len(durations),
                        "min_seconds": min(durations),
                        "max_seconds": max(durations),
                        "avg_seconds": sum(durations) / len(durations),
                        "p95_seconds": self._percentile(durations, 95),
                        "p99_seconds": self._percentile(durations, 99),
                        "total_seconds": sum(durations),
                    }

            return summary

    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile value."""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]

    def clear_metrics(self) -> None:
        """Clear all metrics."""
        with self._lock:
            self.metrics.clear()
            self.counters.clear()
            self.gauges.clear()
            self.histograms.clear()
            self.timers.clear()


class EventLogger:
    """Logs events for analytics and monitoring."""

    def __init__(self, log_file: Optional[Path] = None):
        self.events: deque = deque(maxlen=50000)
        self._lock = threading.RLock()
        self.logger = logging.getLogger(f"{__name__}.EventLogger")

        # Setup structured event logging
        if log_file:
            self.event_file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=10 * 1024 * 1024, backupCount=5
            )
            self.event_file_handler.setFormatter(logging.Formatter("%(message)s"))

            # Create separate logger for events
            self.event_logger = logging.getLogger(f"{__name__}.events")
            self.event_logger.addHandler(self.event_file_handler)
            self.event_logger.setLevel(logging.INFO)
        else:
            self.event_logger = None

    def log_event(self, event: Event) -> None:
        """Log an event."""
        with self._lock:
            self.events.append(event)

            # Log to file if configured
            if self.event_logger:
                event_data = {
                    "timestamp": event.timestamp,
                    "event_type": event.event_type.value,
                    "session_id": event.session_id,
                    "user_id": event.user_id,
                    "properties": event.properties,
                    "context": event.context,
                }
                self.event_logger.info(json.dumps(event_data, default=str))

    def log_command_execution(
        self,
        command: str,
        success: bool,
        duration: float,
        session_id: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Log a command execution event."""
        self.log_event(
            Event(
                event_type=EventType.COMMAND_EXECUTED,
                session_id=session_id,
                properties={
                    "command": command,
                    "success": success,
                    "duration_seconds": duration,
                    **kwargs,
                },
            )
        )

    def log_llm_query(
        self,
        query: str,
        response_time: float,
        model: str,
        success: bool,
        session_id: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Log an LLM query event."""
        self.log_event(
            Event(
                event_type=EventType.LLM_QUERY,
                session_id=session_id,
                properties={
                    "query_length": len(query),
                    "response_time_seconds": response_time,
                    "model": model,
                    "success": success,
                    **kwargs,
                },
            )
        )

    def log_error(
        self,
        error_type: str,
        error_message: str,
        context: Dict[str, Any],
        session_id: Optional[str] = None,
    ) -> None:
        """Log an error event."""
        self.log_event(
            Event(
                event_type=EventType.ERROR_OCCURRED,
                session_id=session_id,
                properties={"error_type": error_type, "error_message": error_message},
                context=context,
            )
        )

    def get_events_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of recent events."""
        cutoff_time = time.time() - (hours * 3600)

        with self._lock:
            recent_events = [e for e in self.events if e.timestamp >= cutoff_time]

            if not recent_events:
                return {"total_events": 0, "period_hours": hours}

            # Analyze events
            by_type = defaultdict(int)
            by_session = defaultdict(int)
            command_stats = {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "avg_duration": 0,
            }

            durations = []

            for event in recent_events:
                by_type[event.event_type.value] += 1

                if event.session_id:
                    by_session[event.session_id] += 1

                if event.event_type == EventType.COMMAND_EXECUTED:
                    command_stats["total"] += 1
                    if event.properties.get("success"):
                        command_stats["successful"] += 1
                    else:
                        command_stats["failed"] += 1

                    duration = event.properties.get("duration_seconds", 0)
                    if duration:
                        durations.append(duration)

            if durations:
                command_stats["avg_duration"] = sum(durations) / len(durations)

            return {
                "total_events": len(recent_events),
                "period_hours": hours,
                "by_type": dict(by_type),
                "unique_sessions": len(by_session),
                "command_stats": command_stats,
                "most_active_session": (
                    max(by_session.items(), key=lambda x: x[1])[0]
                    if by_session
                    else None
                ),
            }


class SessionManager:
    """Manages user sessions for analytics."""

    def __init__(self):
        self.sessions: Dict[str, SessionInfo] = {}
        self._lock = threading.RLock()
        self.logger = logging.getLogger(f"{__name__}.SessionManager")

    def start_session(self, user_agent: Optional[str] = None) -> str:
        """Start a new session."""
        session_id = str(uuid.uuid4())

        with self._lock:
            self.sessions[session_id] = SessionInfo(
                session_id=session_id, start_time=time.time(), user_agent=user_agent
            )

        self.logger.info(f"Started session: {session_id}")
        return session_id

    def end_session(self, session_id: str) -> None:
        """End a session."""
        with self._lock:
            if session_id in self.sessions:
                self.sessions[session_id].end_time = time.time()
                self.logger.info(f"Ended session: {session_id}")

    def update_session(self, session_id: str, **updates) -> None:
        """Update session information."""
        with self._lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                for key, value in updates.items():
                    if hasattr(session, key):
                        if key == "plugins_used" and isinstance(value, str):
                            session.plugins_used.add(value)
                        else:
                            setattr(session, key, value)

    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """Get session information."""
        with self._lock:
            return self.sessions.get(session_id)

    def get_active_sessions(self) -> List[SessionInfo]:
        """Get list of active sessions."""
        with self._lock:
            return [
                session
                for session in self.sessions.values()
                if session.end_time is None
            ]

    def get_session_analytics(self) -> Dict[str, Any]:
        """Get session analytics."""
        with self._lock:
            if not self.sessions:
                return {"total_sessions": 0}

            active_sessions = len(
                [s for s in self.sessions.values() if s.end_time is None]
            )
            total_sessions = len(self.sessions)

            # Calculate session durations
            durations = []
            for session in self.sessions.values():
                if session.end_time:
                    durations.append(session.end_time - session.start_time)

            avg_duration = sum(durations) / len(durations) if durations else 0

            # Commands per session
            commands_per_session = [s.commands_executed for s in self.sessions.values()]
            avg_commands = (
                sum(commands_per_session) / len(commands_per_session)
                if commands_per_session
                else 0
            )

            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "avg_session_duration_seconds": avg_duration,
                "avg_commands_per_session": avg_commands,
                "total_commands": sum(commands_per_session),
                "most_used_plugins": self._get_plugin_usage_stats(),
            }

    def _get_plugin_usage_stats(self) -> Dict[str, int]:
        """Get plugin usage statistics."""
        plugin_counts = defaultdict(int)
        for session in self.sessions.values():
            for plugin in session.plugins_used:
                plugin_counts[plugin] += 1
        return dict(plugin_counts)


class TelemetryManager:
    """Main telemetry manager that coordinates all observability components."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.TelemetryManager")

        # Initialize components
        self.metrics = MetricsCollector()

        # Setup event logging
        event_log_file = self.config.get("event_log_file")
        if event_log_file:
            event_log_file = Path(event_log_file)
        self.events = EventLogger(event_log_file)

        self.sessions = SessionManager()

        # Current session
        self.current_session_id: Optional[str] = None

        # Setup application logging
        self._setup_application_logging()

    def _setup_application_logging(self) -> None:
        """Setup enhanced application logging."""
        log_level = self.config.get("log_level", "INFO")
        log_file = self.config.get("log_file")

        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, log_level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )

        # Add file handler if specified
        if log_file:
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=50 * 1024 * 1024, backupCount=10
            )
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
            logging.getLogger().addHandler(file_handler)

    def start_session(self) -> str:
        """Start a new telemetry session."""
        self.current_session_id = self.sessions.start_session()
        self.events.log_event(
            Event(
                event_type=EventType.USER_SESSION_START,
                session_id=self.current_session_id,
            )
        )
        return self.current_session_id

    def end_session(self) -> None:
        """End current telemetry session."""
        if self.current_session_id:
            self.sessions.end_session(self.current_session_id)
            self.events.log_event(
                Event(
                    event_type=EventType.USER_SESSION_END,
                    session_id=self.current_session_id,
                )
            )
            self.current_session_id = None

    def record_command_execution(
        self, command: str, success: bool, duration: float, **metadata
    ) -> None:
        """Record command execution telemetry."""
        # Update metrics
        self.metrics.increment_counter("commands_executed")
        self.metrics.record_timer("command_duration", duration)

        if success:
            self.metrics.increment_counter("commands_successful")
        else:
            self.metrics.increment_counter("commands_failed")

        # Log event
        self.events.log_command_execution(
            command=command,
            success=success,
            duration=duration,
            session_id=self.current_session_id,
            **metadata,
        )

        # Update session
        if self.current_session_id:
            self.sessions.update_session(
                self.current_session_id,
                commands_executed=self.sessions.get_session(
                    self.current_session_id
                ).commands_executed
                + 1,
            )

    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Get comprehensive telemetry report."""
        return {
            "metrics": self.metrics.get_metrics_summary(),
            "events": self.events.get_events_summary(),
            "sessions": self.sessions.get_session_analytics(),
            "system_info": {
                "python_version": sys.version,
                "platform": sys.platform,
            },
            "timestamp": time.time(),
        }


# Global telemetry manager
_telemetry_manager: Optional[TelemetryManager] = None


def get_telemetry_manager() -> TelemetryManager:
    """Get global telemetry manager instance."""
    global _telemetry_manager
    if _telemetry_manager is None:
        _telemetry_manager = TelemetryManager()
    return _telemetry_manager


def init_telemetry(config: Optional[Dict[str, Any]] = None) -> TelemetryManager:
    """Initialize telemetry with configuration."""
    global _telemetry_manager
    _telemetry_manager = TelemetryManager(config)
    return _telemetry_manager
