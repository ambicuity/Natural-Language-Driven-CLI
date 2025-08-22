"""
Test Phase 4 Production Ready Features
Tests for security, performance, error recovery, telemetry, and enterprise features.
"""

import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch  # noqa: F401

from nlcli.context import Intent, SessionContext
from nlcli.enterprise import (  # noqa: F401
    AuditLogger,
    EnterpriseManager,
    Permission,
    PolicyEngine,
    Role,
    RoleBasedAccessControl,
    User,
    get_enterprise_manager,
)
from nlcli.error_recovery import (
    ErrorCategory,
    ErrorClassifier,
    ErrorContext,
    ErrorRecoveryManager,
    ErrorSeverity,
    RetryConfig,
    get_error_recovery_manager,
    graceful_fallback,
    with_retry,
)
from nlcli.performance import (  # noqa: F401
    PerformanceCache,
    PerformanceProfiler,
    ResourceMonitor,
    cached,
    get_performance_profiler,
    profile_operation,
)
from nlcli.security import (  # noqa: F401
    CommandSanitizer,
    SecurityAuditor,
    SecurityLevel,
    SecurityPolicy,
    VulnerabilityType,
    audit_command_security,
    get_security_auditor,
)
from nlcli.telemetry import (  # noqa: F401
    EventLogger,
    EventType,
    MetricsCollector,
    MetricType,
    SessionManager,
    TelemetryManager,
    get_telemetry_manager,
)


class TestSecurity(unittest.TestCase):
    """Test security auditing features."""

    def setUp(self):
        self.auditor = SecurityAuditor()
        self.context = SessionContext()

    def test_security_auditor_creation(self):
        """Test security auditor creation."""
        self.assertIsInstance(self.auditor, SecurityAuditor)
        self.assertEqual(len(self.auditor.violation_history), 0)

    def test_command_injection_detection(self):
        """Test command injection detection."""
        intent = Intent(
            tool_name="test",
            command="ls; rm -rf /",
            args={},
            explanation="Test command with injection",
        )

        violations = self.auditor.audit_command(intent, self.context)
        self.assertTrue(len(violations) > 0)

        # Check for command injection violation
        injection_violations = [
            v
            for v in violations
            if v.violation_type == VulnerabilityType.COMMAND_INJECTION
        ]
        self.assertTrue(len(injection_violations) > 0)

    def test_path_traversal_detection(self):
        """Test path traversal detection."""
        intent = Intent(
            tool_name="test",
            command="cat ../../etc/passwd",
            args={},
            explanation="Test path traversal command",
        )

        violations = self.auditor.audit_command(intent, self.context)
        traversal_violations = [
            v
            for v in violations
            if v.violation_type == VulnerabilityType.PATH_TRAVERSAL
        ]
        self.assertTrue(len(traversal_violations) > 0)

    def test_privilege_escalation_detection(self):
        """Test privilege escalation detection."""
        intent = Intent(
            tool_name="test",
            command="sudo rm file.txt",
            args={},
            explanation="Test privilege escalation command",
        )

        violations = self.auditor.audit_command(intent, self.context)
        escalation_violations = [
            v
            for v in violations
            if v.violation_type == VulnerabilityType.PRIVILEGE_ESCALATION
        ]
        self.assertTrue(len(escalation_violations) > 0)

    def test_security_policy_enforcement(self):
        """Test security policy enforcement."""
        policy = SecurityPolicy(max_command_length=10, blocked_directories={"/etc"})
        auditor = SecurityAuditor(policy)

        # Test command length limit
        intent = Intent(
            tool_name="test",
            command="this is a very long command that exceeds policy",
            args={},
            explanation="Test long command",
        )
        violations = auditor.audit_command(intent, self.context)
        self.assertTrue(len(violations) > 0)

    def test_command_sanitizer(self):
        """Test command sanitization."""
        sanitizer = CommandSanitizer()

        # Test command with injection
        original = "ls; rm -rf /"
        sanitized, was_modified = sanitizer.sanitize_command(original)

        self.assertTrue(was_modified)
        self.assertNotIn("rm -rf", sanitized)

    def test_security_report_generation(self):
        """Test security report generation."""
        # Generate some violations
        intent = Intent(
            tool_name="test",
            command="sudo ls",
            args={},
            explanation="Test sudo command",
        )
        self.auditor.audit_command(intent, self.context)

        report = self.auditor.get_security_report()
        self.assertEqual(report["status"], "violations_detected")
        self.assertIn("total_violations", report)
        self.assertIn("by_severity", report)


class TestPerformance(unittest.TestCase):
    """Test performance monitoring features."""

    def setUp(self):
        self.profiler = PerformanceProfiler()
        self.cache = PerformanceCache(max_size=10)

    def test_performance_profiler_creation(self):
        """Test performance profiler creation."""
        self.assertIsInstance(self.profiler, PerformanceProfiler)
        self.assertEqual(len(self.profiler.metrics), 0)

    def test_operation_profiling(self):
        """Test operation profiling."""
        with self.profiler.profile_operation("test_operation"):
            time.sleep(0.01)  # Small delay to measure

        self.assertEqual(len(self.profiler.metrics), 1)
        metric = self.profiler.metrics[0]
        self.assertEqual(metric.operation, "test_operation")
        self.assertTrue(metric.success)
        self.assertGreater(metric.duration, 0)

    def test_performance_cache(self):
        """Test performance cache."""
        # Test cache miss
        result = self.cache.get("key1")
        self.assertIsNone(result)

        # Test cache put and hit
        self.cache.put("key1", "value1")
        result = self.cache.get("key1")
        self.assertEqual(result, "value1")

        # Test cache stats
        stats = self.cache.get_stats()
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)

    def test_cached_decorator(self):
        """Test cached decorator."""
        call_count = 0

        @cached(ttl_seconds=1)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call - cache miss
        result1 = expensive_function(5)
        self.assertEqual(result1, 10)
        self.assertEqual(call_count, 1)

        # Second call - cache hit
        result2 = expensive_function(5)
        self.assertEqual(result2, 10)
        self.assertEqual(call_count, 1)  # Should not increment

    def test_resource_monitoring(self):
        """Test resource monitoring."""
        monitor = ResourceMonitor(sampling_interval=0.1)

        # Start monitoring briefly
        monitor.start_monitoring()
        time.sleep(0.2)
        monitor.stop_monitoring()

        # Check that some data was collected
        current = monitor.get_current_usage()
        self.assertIsNotNone(current)
        self.assertGreater(current.cpu_percent, -1)  # Should be >= 0
        self.assertGreater(current.memory_percent, 0)

    def test_metrics_summary(self):
        """Test performance metrics summary."""
        # Add some test metrics
        with self.profiler.profile_operation("op1"):
            time.sleep(0.01)

        with self.profiler.profile_operation("op2"):
            time.sleep(0.02)

        summary = self.profiler.get_metrics_summary()
        self.assertEqual(summary["total_operations"], 2)
        self.assertIn("duration_stats", summary)
        self.assertIn("by_operation", summary)


class TestErrorRecovery(unittest.TestCase):
    """Test error recovery features."""

    def setUp(self):
        self.classifier = ErrorClassifier()
        self.recovery_manager = ErrorRecoveryManager()

    def test_error_classification(self):
        """Test error classification."""
        # Test network error
        network_error = ConnectionError("Connection refused")
        context = ErrorContext(operation="test_network")
        category, severity = self.classifier.classify_error(network_error, context)

        self.assertEqual(category, ErrorCategory.NETWORK)
        self.assertEqual(severity, ErrorSeverity.HIGH)

        # Test filesystem error
        fs_error = FileNotFoundError("No such file or directory")
        category, severity = self.classifier.classify_error(fs_error, context)

        self.assertEqual(category, ErrorCategory.FILESYSTEM)
        self.assertEqual(severity, ErrorSeverity.MEDIUM)

    def test_recovery_actions(self):
        """Test recovery action suggestions."""
        actions = self.classifier.get_recovery_actions(ErrorCategory.NETWORK)
        self.assertTrue(len(actions) > 0)

        # Check for expected recovery actions
        action_types = [action.action_type for action in actions]
        self.assertIn("retry_with_backoff", action_types)

    def test_error_handling(self):
        """Test error handling and recovery."""
        context = ErrorContext(operation="test_operation")
        test_error = ValueError("Test error")

        _result = self.recovery_manager.handle_error(test_error, context)  # noqa: F841

        # Check that error was recorded
        self.assertEqual(len(self.recovery_manager.error_history), 1)
        recorded_error = self.recovery_manager.error_history[0]
        self.assertEqual(recorded_error.error_message, "Test error")

    def test_retry_config(self):
        """Test retry configuration."""
        config = RetryConfig(max_attempts=3, base_delay=1.0)

        # Test delay calculation
        delay1 = config.get_delay(1)
        delay2 = config.get_delay(2)
        delay3 = config.get_delay(3)

        self.assertGreater(delay2, delay1)
        self.assertGreater(delay3, delay2)

    def test_with_retry_decorator(self):
        """Test retry decorator."""
        call_count = 0

        @with_retry(retry_config=RetryConfig(max_attempts=3, base_delay=0.001))
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Simulated failure")
            return "success"

        # Should succeed on third attempt
        result = failing_function()
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)

    def test_graceful_fallback(self):
        """Test graceful fallback decorator."""

        @graceful_fallback(fallback_value="fallback", log_error=False)
        def failing_function():
            raise ValueError("Always fails")

        result = failing_function()
        self.assertEqual(result, "fallback")


class TestTelemetry(unittest.TestCase):
    """Test telemetry and metrics features."""

    def setUp(self):
        self.telemetry = TelemetryManager()
        self.metrics = MetricsCollector()

    def test_metrics_collector(self):
        """Test metrics collection."""
        # Test counter
        self.metrics.increment_counter("test_counter", 5)
        self.assertEqual(self.metrics.counters["test_counter"], 5)

        # Test gauge
        self.metrics.set_gauge("test_gauge", 42.5)
        self.assertEqual(self.metrics.gauges["test_gauge"], 42.5)

        # Test histogram
        self.metrics.record_histogram("test_histogram", 10.0)
        self.assertEqual(len(self.metrics.histograms["test_histogram"]), 1)

        # Test timer
        self.metrics.record_timer("test_timer", 1.5)
        self.assertEqual(len(self.metrics.timers["test_timer"]), 1)

    def test_event_logging(self):
        """Test event logging."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        # Create event logger after the file is closed
        event_logger = EventLogger(Path(temp_path))

        event_logger.log_command_execution(command="ls -la", success=True, duration=0.5)

        # Check that event was recorded
        self.assertEqual(len(event_logger.events), 1)

        # Cleanup
        try:
            os.unlink(temp_path)
        except (OSError, PermissionError):
            # On Windows, the file might still be in use
            pass

    def test_session_management(self):
        """Test session management."""
        session_manager = SessionManager()

        # Start session
        session_id = session_manager.start_session()
        self.assertTrue(session_id)

        # Update session
        session_manager.update_session(
            session_id, commands_executed=5, plugins_used="test_plugin"
        )

        # Get session
        session = session_manager.get_session(session_id)
        self.assertIsNotNone(session)
        self.assertEqual(session.commands_executed, 5)
        self.assertIn("test_plugin", session.plugins_used)

    def test_telemetry_manager(self):
        """Test telemetry manager."""
        # Start session
        session_id = self.telemetry.start_session()
        self.assertIsNotNone(session_id)

        # Record command execution
        self.telemetry.record_command_execution(
            command="test command", success=True, duration=1.0
        )

        # Get report
        report = self.telemetry.get_comprehensive_report()
        self.assertIn("metrics", report)
        self.assertIn("events", report)
        self.assertIn("sessions", report)

        # End session
        self.telemetry.end_session()


class TestEnterprise(unittest.TestCase):
    """Test enterprise features."""

    def setUp(self):
        self.rbac = RoleBasedAccessControl()
        self.policy_engine = PolicyEngine()

        # Create test user
        self.test_user = User(
            user_id="test_user",
            username="testuser",
            email="test@example.com",
            roles={Role.USER},
            created_at=time.time(),
        )

    def test_rbac_permissions(self):
        """Test role-based access control."""
        # Test user permissions
        has_execute = self.rbac.user_has_permission(
            self.test_user, Permission.EXECUTE_COMMAND
        )
        self.assertTrue(has_execute)

        has_manage_users = self.rbac.user_has_permission(
            self.test_user, Permission.MANAGE_USERS
        )
        self.assertFalse(has_manage_users)

        # Test admin permissions
        admin_user = User(
            user_id="admin",
            username="admin",
            email="admin@example.com",
            roles={Role.ADMIN},
            created_at=time.time(),
        )

        has_manage_users = self.rbac.user_has_permission(
            admin_user, Permission.MANAGE_USERS
        )
        self.assertTrue(has_manage_users)

    def test_audit_logging(self):
        """Test audit logging."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            audit_logger = AuditLogger(Path(f.name))

            # Log command execution
            audit_logger.log_command_execution(
                user_id="test_user", command="ls -la", success=True
            )

            # Verify audit file exists and has content
            self.assertTrue(Path(f.name).exists())

            # Test integrity verification
            integrity = audit_logger.verify_audit_integrity()
            self.assertEqual(integrity["status"], "completed")
            self.assertGreater(integrity["total_entries"], 0)

        # Cleanup
        os.unlink(f.name)

    def test_policy_engine(self):
        """Test policy engine."""
        # Test command evaluation
        result = self.policy_engine.evaluate_command(
            "rm -rf dangerous_file", self.test_user
        )

        # Should have violations due to dangerous command
        self.assertIn("violations", result)

        # Test file access evaluation
        file_result = self.policy_engine.evaluate_file_access(
            "/etc/passwd", "read", self.test_user
        )

        # Should be blocked
        self.assertFalse(file_result["allowed"])
        self.assertTrue(len(file_result["violations"]) > 0)

    def test_enterprise_manager(self):
        """Test enterprise manager."""
        enterprise = EnterpriseManager()

        # Create user
        user = enterprise.create_user("testuser", "test@example.com", {Role.USER})
        self.assertIsNotNone(user)

        # Authenticate user
        auth_user = enterprise.authenticate_user("testuser")
        self.assertIsNotNone(auth_user)

        # Check permission
        can_execute = enterprise.check_permission(Permission.EXECUTE_COMMAND)
        self.assertTrue(can_execute)

        # Evaluate command
        cmd_result = enterprise.evaluate_command("ls -la")
        # Should be allowed for basic command
        self.assertTrue(cmd_result.get("allowed", True))

    def test_configuration_management(self):
        """Test configuration management."""
        from nlcli.enterprise import ConfigurationManager

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            config_manager = ConfigurationManager(Path(f.name))

            # Test setting and getting config values
            config_manager.set_config_value("test.setting", "test_value")
            value = config_manager.get_config_value("test.setting")
            self.assertEqual(value, "test_value")

            # Test default values
            default_value = config_manager.get_config_value(
                "nonexistent.setting", "default"
            )
            self.assertEqual(default_value, "default")

        # Cleanup
        os.unlink(f.name)


class TestIntegration(unittest.TestCase):
    """Test integration between Phase 4 modules."""

    def test_enhanced_safety_check(self):
        """Test enhanced safety check integration."""
        from nlcli.safety import enhanced_safety_check

        context = SessionContext()

        # Test safe command
        safe_intent = Intent(
            tool_name="ls", command="ls -la", args={}, explanation="List files"
        )
        is_safe, message, violations = enhanced_safety_check(safe_intent, context)
        self.assertTrue(is_safe)

        # Test dangerous command
        dangerous_intent = Intent(
            tool_name="rm", command="rm -rf /", args={}, explanation="Remove all files"
        )
        is_safe, message, violations = enhanced_safety_check(dangerous_intent, context)
        self.assertFalse(is_safe)
        self.assertTrue(len(violations) > 0)

    def test_global_managers(self):
        """Test global manager instances."""
        # Import functions that aren't already imported at module level

        # Test that managers are singletons
        auditor1 = get_security_auditor()
        auditor2 = get_security_auditor()
        self.assertIs(auditor1, auditor2)

        profiler1 = get_performance_profiler()
        profiler2 = get_performance_profiler()
        self.assertIs(profiler1, profiler2)

        recovery1 = get_error_recovery_manager()
        recovery2 = get_error_recovery_manager()
        self.assertIs(recovery1, recovery2)

        telemetry1 = get_telemetry_manager()
        telemetry2 = get_telemetry_manager()
        self.assertIs(telemetry1, telemetry2)

        enterprise1 = get_enterprise_manager()
        enterprise2 = get_enterprise_manager()
        self.assertIs(enterprise1, enterprise2)


if __name__ == "__main__":
    unittest.main()
