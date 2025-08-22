"""
Enhanced Security Module for Production-Ready CLI.
Implements comprehensive security auditing, vulnerability scanning,
and policy enforcement.
"""

import logging
import re
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from nlcli.context import Intent, SessionContext


class SecurityLevel(Enum):
    """Security levels for command execution."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class VulnerabilityType(Enum):
    """Types of security vulnerabilities."""

    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    SYSTEM_MODIFICATION = "system_modification"
    NETWORK_ACCESS = "network_access"


@dataclass
class SecurityViolation:
    """Represents a security violation."""

    violation_type: VulnerabilityType
    severity: SecurityLevel
    description: str
    command: str
    recommendation: str
    timestamp: float


@dataclass
class SecurityPolicy:
    """Security policy configuration."""

    max_command_length: int = 1000
    allowed_file_extensions: Set[str] = None
    blocked_directories: Set[str] = None
    max_file_size_mb: int = 100
    allow_network_commands: bool = True
    allow_system_modifications: bool = False
    require_confirmation_for: Set[VulnerabilityType] = None

    def __post_init__(self):
        if self.allowed_file_extensions is None:
            self.allowed_file_extensions = {
                ".txt",
                ".log",
                ".json",
                ".yaml",
                ".yml",
                ".md",
                ".csv",
                ".tsv",
            }
        if self.blocked_directories is None:
            self.blocked_directories = {
                "/etc/shadow",
                "/etc/passwd",
                "/root",
                "/boot",
                "/sys",
                "/proc/sys",
            }
        if self.require_confirmation_for is None:
            self.require_confirmation_for = {
                VulnerabilityType.PRIVILEGE_ESCALATION,
                VulnerabilityType.SYSTEM_MODIFICATION,
                VulnerabilityType.DATA_EXFILTRATION,
            }


class SecurityAuditor:
    """Enhanced security auditor for comprehensive threat detection."""

    def __init__(self, policy: Optional[SecurityPolicy] = None):
        self.policy = policy or SecurityPolicy()
        self.logger = logging.getLogger(f"{__name__}.SecurityAuditor")
        self.violation_history: List[SecurityViolation] = []

        # Enhanced dangerous patterns with severity levels
        self.vulnerability_patterns = {
            VulnerabilityType.COMMAND_INJECTION: [
                (
                    r";\s*rm\s+-rf",
                    SecurityLevel.CRITICAL,
                    "Command chaining with destructive rm",
                ),
                (r"\|\s*sh\s*$", SecurityLevel.HIGH, "Pipe to shell execution"),
                (r"\$\([^)]*\)", SecurityLevel.MEDIUM, "Command substitution"),
                (r"`[^`]*`", SecurityLevel.MEDIUM, "Backtick command execution"),
                (r"eval\s+", SecurityLevel.HIGH, "Eval command execution"),
            ],
            VulnerabilityType.PATH_TRAVERSAL: [
                (r"\.\./", SecurityLevel.HIGH, "Directory traversal attempt"),
                (r"/\.\.", SecurityLevel.HIGH, "Path traversal pattern"),
                (r"~.*/", SecurityLevel.MEDIUM, "Home directory access"),
            ],
            VulnerabilityType.PRIVILEGE_ESCALATION: [
                (r"sudo\s+", SecurityLevel.HIGH, "Privilege escalation via sudo"),
                (r"su\s+", SecurityLevel.HIGH, "User switching"),
                (
                    r"chmod\s+[4567]\d\d",
                    SecurityLevel.HIGH,
                    "Setuid/setgid permissions",
                ),
            ],
            VulnerabilityType.DATA_EXFILTRATION: [
                (r"curl.*-d.*@", SecurityLevel.HIGH, "Data upload via curl"),
                (r"wget.*--post", SecurityLevel.HIGH, "Data upload via wget"),
                (r"scp\s+.*:", SecurityLevel.MEDIUM, "Secure copy operation"),
                (r"rsync.*--delete", SecurityLevel.HIGH, "Destructive sync operation"),
            ],
            VulnerabilityType.SYSTEM_MODIFICATION: [
                (r"rm\s+-rf\s+/", SecurityLevel.CRITICAL, "Root filesystem deletion"),
                (r"mkfs\.", SecurityLevel.CRITICAL, "Filesystem formatting"),
                (r"dd\s+.*of=/dev/", SecurityLevel.CRITICAL, "Direct device write"),
                (r"fdisk", SecurityLevel.HIGH, "Disk partitioning"),
            ],
            VulnerabilityType.NETWORK_ACCESS: [
                (r"nc\s+-l", SecurityLevel.HIGH, "Network listener"),
                (r"netcat\s+-l", SecurityLevel.HIGH, "Netcat listener"),
                (r"python.*-m.*http\.server", SecurityLevel.MEDIUM, "HTTP server"),
                (r"telnet\s+", SecurityLevel.MEDIUM, "Telnet connection"),
            ],
        }

    def audit_command(
        self, intent: Intent, context: SessionContext
    ) -> List[SecurityViolation]:
        """
        Perform comprehensive security audit on a command.

        Args:
            intent: Command intent to audit
            context: Session context

        Returns:
            List of security violations found
        """
        violations = []
        command = intent.command

        # Check command length
        if len(command) > self.policy.max_command_length:
            violations.append(
                SecurityViolation(
                    violation_type=VulnerabilityType.COMMAND_INJECTION,
                    severity=SecurityLevel.MEDIUM,
                    description=f"Command length ({len(command)}) exceeds policy limit",
                    command=command,
                    recommendation="Break down into smaller commands",
                    timestamp=time.time(),
                )
            )

        # Scan for vulnerability patterns
        for vuln_type, patterns in self.vulnerability_patterns.items():
            for pattern, severity, description in patterns:
                if re.search(pattern, command, re.IGNORECASE):
                    violations.append(
                        SecurityViolation(
                            violation_type=vuln_type,
                            severity=severity,
                            description=description,
                            command=command,
                            recommendation=self._get_recommendation(vuln_type),
                            timestamp=time.time(),
                        )
                    )

        # Check file paths
        violations.extend(self._audit_file_paths(command))

        # Store violations for analysis
        self.violation_history.extend(violations)

        return violations

    def _audit_file_paths(self, command: str) -> List[SecurityViolation]:
        """Audit file paths in command for security violations."""
        violations = []

        # Extract file paths
        path_patterns = [
            r"(?:^|\s)(/[^\s]*)",  # Absolute paths
            r"(?:^|\s)(~[^\s]*)",  # Home directory paths
            r"(?:^|\s)(\./[^\s]*)",  # Relative paths
        ]

        paths = set()
        for pattern in path_patterns:
            matches = re.findall(pattern, command)
            paths.update(matches)

        for path_str in paths:
            try:
                path = Path(path_str).resolve()

                # Check for blocked directories
                for blocked in self.policy.blocked_directories:
                    if str(path).startswith(blocked):
                        violations.append(
                            SecurityViolation(
                                violation_type=VulnerabilityType.PATH_TRAVERSAL,
                                severity=SecurityLevel.HIGH,
                                description=f"Access to blocked directory: {blocked}",
                                command=command,
                                recommendation="Use allowed directories only",
                                timestamp=time.time(),
                            )
                        )

            except Exception:
                # Path resolution failed - treat as suspicious
                violations.append(
                    SecurityViolation(
                        violation_type=VulnerabilityType.PATH_TRAVERSAL,
                        severity=SecurityLevel.MEDIUM,
                        description=f"Suspicious or invalid path: {path_str}",
                        command=command,
                        recommendation="Use valid, absolute paths",
                        timestamp=time.time(),
                    )
                )

        return violations

    def _get_recommendation(self, vuln_type: VulnerabilityType) -> str:
        """Get security recommendation for vulnerability type."""
        recommendations = {
            VulnerabilityType.COMMAND_INJECTION: (
                "Use parameterized commands and avoid shell metacharacters"
            ),
            VulnerabilityType.PATH_TRAVERSAL: (
                "Use absolute paths within allowed directories"
            ),
            VulnerabilityType.PRIVILEGE_ESCALATION: (
                "Avoid privilege escalation; use appropriate user permissions"
            ),
            VulnerabilityType.DATA_EXFILTRATION: (
                "Review data transfer operations for necessity"
            ),
            VulnerabilityType.SYSTEM_MODIFICATION: (
                "Use read-only operations when possible"
            ),
            VulnerabilityType.NETWORK_ACCESS: (
                "Ensure network operations are authorized and secure"
            ),
        }
        return recommendations.get(
            vuln_type, "Review command for security implications"
        )

    def get_security_report(self) -> Dict:
        """Generate security audit report."""
        if not self.violation_history:
            return {
                "status": "clean",
                "violations": 0,
                "summary": "No security violations detected",
            }

        # Analyze violations
        by_severity = {}
        by_type = {}

        for violation in self.violation_history:
            severity = violation.severity.value
            vuln_type = violation.violation_type.value

            by_severity[severity] = by_severity.get(severity, 0) + 1
            by_type[vuln_type] = by_type.get(vuln_type, 0) + 1

        # Determine overall risk level
        risk_level = "low"
        if by_severity.get("critical", 0) > 0:
            risk_level = "critical"
        elif by_severity.get("high", 0) > 0:
            risk_level = "high"
        elif by_severity.get("medium", 0) > 0:
            risk_level = "medium"

        return {
            "status": "violations_detected",
            "risk_level": risk_level,
            "total_violations": len(self.violation_history),
            "by_severity": by_severity,
            "by_type": by_type,
            "recent_violations": [
                {
                    "type": v.violation_type.value,
                    "severity": v.severity.value,
                    "description": v.description,
                    "recommendation": v.recommendation,
                    "timestamp": v.timestamp,
                }
                for v in self.violation_history[-10:]  # Last 10 violations
            ],
        }

    def clear_history(self) -> None:
        """Clear violation history."""
        self.violation_history.clear()


class CommandSanitizer:
    """Sanitizes commands to remove potential security threats."""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.CommandSanitizer")

        # Characters that need escaping
        self.shell_metacharacters = {
            ";",
            "&",
            "|",
            "(",
            ")",
            "<",
            ">",
            "`",
            "$",
            '"',
            "'",
            "\\",
            "*",
            "?",
            "[",
            "]",
        }

    def sanitize_command(self, command: str) -> Tuple[str, bool]:
        """
        Sanitize a command to remove security threats.

        Args:
            command: Original command

        Returns:
            Tuple of (sanitized_command, was_modified)
        """
        original = command
        sanitized = command

        # Remove dangerous command chaining
        sanitized = re.sub(r";\s*[^;]*(?:rm|del|format)", "", sanitized)

        # Remove pipe to shell
        sanitized = re.sub(r"\|\s*(?:sh|bash|zsh|csh)$", "", sanitized)

        # Remove command substitution
        sanitized = re.sub(r"\$\([^)]*\)", "", sanitized)
        sanitized = re.sub(r"`[^`]*`", "", sanitized)

        # Clean up whitespace
        sanitized = " ".join(sanitized.split())

        was_modified = original != sanitized

        if was_modified:
            self.logger.warning(f"Command sanitized: {original} -> {sanitized}")

        return sanitized, was_modified


# Global security auditor instance
_security_auditor: Optional[SecurityAuditor] = None


def get_security_auditor() -> SecurityAuditor:
    """Get global security auditor instance."""
    global _security_auditor
    if _security_auditor is None:
        _security_auditor = SecurityAuditor()
    return _security_auditor


def audit_command_security(
    intent: Intent, context: SessionContext
) -> List[SecurityViolation]:
    """Convenience function to audit command security."""
    return get_security_auditor().audit_command(intent, context)
