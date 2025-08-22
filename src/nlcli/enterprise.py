"""
Enterprise Features Module.
Implements role-based access control, audit trails, policy enforcement,
and configuration management.
"""

import hashlib
import json
import logging
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Set


class Role(Enum):
    """User roles for access control."""

    ADMIN = "admin"
    POWER_USER = "power_user"
    USER = "user"
    RESTRICTED = "restricted"
    READ_ONLY = "read_only"


class Permission(Enum):
    """Permissions for operations."""

    EXECUTE_COMMAND = "execute_command"
    READ_FILES = "read_files"
    WRITE_FILES = "write_files"
    DELETE_FILES = "delete_files"
    NETWORK_ACCESS = "network_access"
    SYSTEM_COMMANDS = "system_commands"
    INSTALL_PACKAGES = "install_packages"
    MANAGE_USERS = "manage_users"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    MANAGE_POLICIES = "manage_policies"
    USE_LLM = "use_llm"
    MANAGE_PLUGINS = "manage_plugins"


class AuditAction(Enum):
    """Actions that can be audited."""

    LOGIN = "login"
    LOGOUT = "logout"
    COMMAND_EXECUTED = "command_executed"
    FILE_ACCESSED = "file_accessed"
    POLICY_CHANGED = "policy_changed"
    USER_CREATED = "user_created"
    USER_DELETED = "user_deleted"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"
    SECURITY_VIOLATION = "security_violation"
    PLUGIN_LOADED = "plugin_loaded"
    CONFIG_CHANGED = "config_changed"


@dataclass
class User:
    """Enterprise user with roles and metadata."""

    user_id: str
    username: str
    email: Optional[str]
    roles: Set[Role]
    created_at: float
    last_login: Optional[float] = None
    active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    password_hash: Optional[str] = None


@dataclass
class AuditLogEntry:
    """Immutable audit log entry."""

    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    action: AuditAction = AuditAction.COMMAND_EXECUTED
    resource: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    checksum: Optional[str] = field(init=False)

    def __post_init__(self):
        """Calculate checksum for integrity verification."""
        # Create checksum of all fields except checksum itself
        data = {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "action": self.action.value,
            "resource": self.resource,
            "details": self.details,
            "success": self.success,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
        }
        self.checksum = hashlib.sha256(
            json.dumps(data, sort_keys=True, default=str).encode()
        ).hexdigest()


@dataclass
class Policy:
    """Security and operational policy."""

    policy_id: str
    name: str
    description: str
    rules: Dict[str, Any]
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    active: bool = True
    version: int = 1


class RoleBasedAccessControl:
    """Role-based access control system."""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.RBAC")

        # Default role permissions
        self.role_permissions = {
            Role.ADMIN: {
                Permission.EXECUTE_COMMAND,
                Permission.READ_FILES,
                Permission.WRITE_FILES,
                Permission.DELETE_FILES,
                Permission.NETWORK_ACCESS,
                Permission.SYSTEM_COMMANDS,
                Permission.INSTALL_PACKAGES,
                Permission.MANAGE_USERS,
                Permission.VIEW_AUDIT_LOGS,
                Permission.MANAGE_POLICIES,
                Permission.USE_LLM,
                Permission.MANAGE_PLUGINS,
            },
            Role.POWER_USER: {
                Permission.EXECUTE_COMMAND,
                Permission.READ_FILES,
                Permission.WRITE_FILES,
                Permission.DELETE_FILES,
                Permission.NETWORK_ACCESS,
                Permission.SYSTEM_COMMANDS,
                Permission.USE_LLM,
                Permission.MANAGE_PLUGINS,
            },
            Role.USER: {
                Permission.EXECUTE_COMMAND,
                Permission.READ_FILES,
                Permission.WRITE_FILES,
                Permission.NETWORK_ACCESS,
                Permission.USE_LLM,
            },
            Role.RESTRICTED: {Permission.READ_FILES, Permission.USE_LLM},
            Role.READ_ONLY: {Permission.READ_FILES},
        }

    def user_has_permission(self, user: User, permission: Permission) -> bool:
        """Check if user has specific permission."""
        if not user.active:
            return False

        for role in user.roles:
            if permission in self.role_permissions.get(role, set()):
                return True

        return False

    def get_user_permissions(self, user: User) -> Set[Permission]:
        """Get all permissions for a user."""
        permissions = set()

        if user.active:
            for role in user.roles:
                permissions.update(self.role_permissions.get(role, set()))

        return permissions

    def add_role_permission(self, role: Role, permission: Permission) -> None:
        """Add permission to role."""
        if role not in self.role_permissions:
            self.role_permissions[role] = set()
        self.role_permissions[role].add(permission)
        self.logger.info(f"Added permission {permission.value} to role {role.value}")

    def remove_role_permission(self, role: Role, permission: Permission) -> None:
        """Remove permission from role."""
        if role in self.role_permissions:
            self.role_permissions[role].discard(permission)
            self.logger.info(
                f"Removed permission {permission.value} from role {role.value}"
            )


class AuditLogger:
    """Immutable audit logging system."""

    def __init__(self, audit_file: Optional[Path] = None):
        self.audit_file = audit_file or Path("nlcli_audit.log")
        self.logger = logging.getLogger(f"{__name__}.AuditLogger")
        self._lock = threading.Lock()

        # Ensure audit file exists and is secure
        self._initialize_audit_file()

    def _initialize_audit_file(self) -> None:
        """Initialize audit file with secure permissions."""
        if not self.audit_file.exists():
            self.audit_file.touch(mode=0o600)  # Read/write for owner only

        # Verify file permissions
        stat_info = self.audit_file.stat()
        if stat_info.st_mode & 0o077:  # Check if readable by group/others
            self.logger.warning("Audit file has insecure permissions")

    def log_audit_entry(self, entry: AuditLogEntry) -> None:
        """Log an audit entry (immutable)."""
        with self._lock:
            # Convert entry to JSON
            entry_json = json.dumps(asdict(entry), default=str)

            # Append to audit file
            with open(self.audit_file, "a") as f:
                f.write(f"{entry_json}\n")

            # Log to application logger
            self.logger.info(
                f"AUDIT: {entry.action.value} by {entry.user_id} on {entry.resource} "
                f"{'SUCCESS' if entry.success else 'FAILED'}"
            )

    def log_command_execution(
        self,
        user_id: str,
        command: str,
        success: bool,
        session_id: Optional[str] = None,
        **details,
    ) -> None:
        """Log command execution."""
        entry = AuditLogEntry(
            user_id=user_id,
            session_id=session_id,
            action=AuditAction.COMMAND_EXECUTED,
            resource=command,
            success=success,
            details=details,
        )
        self.log_audit_entry(entry)

    def log_permission_check(
        self,
        user_id: str,
        permission: Permission,
        granted: bool,
        resource: Optional[str] = None,
        **details,
    ) -> None:
        """Log permission check."""
        action = (
            AuditAction.PERMISSION_GRANTED if granted else AuditAction.PERMISSION_DENIED
        )
        entry = AuditLogEntry(
            user_id=user_id,
            action=action,
            resource=resource,
            success=granted,
            details={"permission": permission.value, **details},
        )
        self.log_audit_entry(entry)

    def log_security_violation(
        self, user_id: str, violation_type: str, resource: str, **details
    ) -> None:
        """Log security violation."""
        entry = AuditLogEntry(
            user_id=user_id,
            action=AuditAction.SECURITY_VIOLATION,
            resource=resource,
            success=False,
            details={"violation_type": violation_type, **details},
        )
        self.log_audit_entry(entry)

    def verify_audit_integrity(self) -> Dict[str, Any]:
        """Verify audit log integrity."""
        if not self.audit_file.exists():
            return {"status": "no_audit_file", "entries_checked": 0}

        valid_entries = 0
        invalid_entries = 0
        total_entries = 0
        errors = []

        try:
            with open(self.audit_file, "r") as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue

                    total_entries += 1

                    try:
                        entry_data = json.loads(line.strip())

                        # Verify checksum
                        stored_checksum = entry_data.pop("checksum", None)
                        calculated_checksum = hashlib.sha256(
                            json.dumps(entry_data, sort_keys=True, default=str).encode()
                        ).hexdigest()

                        if stored_checksum == calculated_checksum:
                            valid_entries += 1
                        else:
                            invalid_entries += 1
                            errors.append(f"Line {line_num}: Checksum mismatch")

                    except json.JSONDecodeError as e:
                        invalid_entries += 1
                        errors.append(f"Line {line_num}: JSON decode error: {e}")

        except Exception as e:
            return {"status": "error", "error": str(e)}

        return {
            "status": "completed",
            "total_entries": total_entries,
            "valid_entries": valid_entries,
            "invalid_entries": invalid_entries,
            "integrity_rate": (
                valid_entries / total_entries if total_entries > 0 else 1.0
            ),
            "errors": errors[:10],  # Limit error list
        }


class PolicyEngine:
    """Policy enforcement engine."""

    def __init__(self):
        self.policies: Dict[str, Policy] = {}
        self.logger = logging.getLogger(f"{__name__}.PolicyEngine")
        self._lock = threading.RLock()

        # Load default policies
        self._load_default_policies()

    def _load_default_policies(self) -> None:
        """Load default security policies."""
        # Command execution policy
        self.add_policy(
            Policy(
                policy_id="command_execution",
                name="Command Execution Policy",
                description="Controls command execution behavior",
                rules={
                    "max_command_length": 1000,
                    "require_confirmation": ["rm", "del", "format", "mkfs"],
                    "blocked_commands": [
                        "rm -rf /",
                        ":(){ :|:& };:",
                        "dd if=/dev/random",
                    ],
                    "allowed_directories": ["/home", "/tmp", "/var/tmp"],
                    "max_execution_time": 300,  # 5 minutes
                },
            )
        )

        # File access policy
        self.add_policy(
            Policy(
                policy_id="file_access",
                name="File Access Policy",
                description="Controls file system access",
                rules={
                    "blocked_paths": ["/etc/shadow", "/etc/passwd", "/root"],
                    "max_file_size_mb": 100,
                    "allowed_extensions": [
                        ".txt",
                        ".log",
                        ".json",
                        ".yaml",
                        ".yml",
                        ".md",
                    ],
                    "require_confirmation_size_mb": 50,
                },
            )
        )

        # Network access policy
        self.add_policy(
            Policy(
                policy_id="network_access",
                name="Network Access Policy",
                description="Controls network operations",
                rules={
                    "allowed_protocols": ["http", "https", "ftp"],
                    "blocked_domains": ["malicious-site.com"],
                    "require_confirmation_downloads": True,
                    "max_download_size_mb": 1000,
                },
            )
        )

    def add_policy(self, policy: Policy) -> None:
        """Add or update a policy."""
        with self._lock:
            self.policies[policy.policy_id] = policy
            self.logger.info(f"Added/updated policy: {policy.name}")

    def get_policy(self, policy_id: str) -> Optional[Policy]:
        """Get policy by ID."""
        with self._lock:
            return self.policies.get(policy_id)

    def evaluate_command(self, command: str, user: User) -> Dict[str, Any]:
        """Evaluate command against policies."""
        violations = []
        recommendations = []

        # Check command execution policy
        cmd_policy = self.get_policy("command_execution")
        if cmd_policy:
            rules = cmd_policy.rules

            # Check command length
            if len(command) > rules.get("max_command_length", 1000):
                violations.append("Command exceeds maximum length")

            # Check for blocked commands
            for blocked in rules.get("blocked_commands", []):
                if blocked in command:
                    violations.append(f"Blocked command pattern: {blocked}")

            # Check for commands requiring confirmation
            for confirm_cmd in rules.get("require_confirmation", []):
                if confirm_cmd in command:
                    recommendations.append(
                        f"Command '{confirm_cmd}' requires confirmation"
                    )

        return {
            "allowed": len(violations) == 0,
            "violations": violations,
            "recommendations": recommendations,
        }

    def evaluate_file_access(
        self, file_path: str, operation: str, user: User
    ) -> Dict[str, Any]:
        """Evaluate file access against policies."""
        violations = []
        recommendations = []

        file_policy = self.get_policy("file_access")
        if file_policy:
            rules = file_policy.rules

            # Check blocked paths
            for blocked_path in rules.get("blocked_paths", []):
                if file_path.startswith(blocked_path):
                    violations.append(f"Access to blocked path: {blocked_path}")

            # Check file extension for write operations
            if operation in ["write", "create"]:
                allowed_exts = rules.get("allowed_extensions", [])
                if allowed_exts:
                    file_ext = Path(file_path).suffix
                    if file_ext not in allowed_exts:
                        violations.append(f"File extension not allowed: {file_ext}")

        return {
            "allowed": len(violations) == 0,
            "violations": violations,
            "recommendations": recommendations,
        }

    def get_policy_summary(self) -> Dict[str, Any]:
        """Get summary of all policies."""
        with self._lock:
            return {
                "total_policies": len(self.policies),
                "active_policies": len([p for p in self.policies.values() if p.active]),
                "policies": [
                    {
                        "id": p.policy_id,
                        "name": p.name,
                        "description": p.description,
                        "active": p.active,
                        "version": p.version,
                    }
                    for p in self.policies.values()
                ],
            }


class ConfigurationManager:
    """Enterprise configuration management."""

    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or Path("nlcli_enterprise.json")
        self.config: Dict[str, Any] = {}
        self.logger = logging.getLogger(f"{__name__}.ConfigurationManager")
        self._lock = threading.RLock()

        # Load configuration
        self.load_configuration()

    def load_configuration(self) -> None:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    self.config = json.load(f)
                self.logger.info(f"Loaded configuration from {self.config_file}")
            except Exception as e:
                self.logger.error(f"Failed to load configuration: {e}")
                self._set_default_configuration()
        else:
            self._set_default_configuration()

    def _set_default_configuration(self) -> None:
        """Set default enterprise configuration."""
        self.config = {
            "enterprise": {
                "enabled": False,
                "organization": "Default Organization",
                "audit_retention_days": 365,
                "require_user_authentication": False,
                "default_user_role": "user",
                "session_timeout_minutes": 60,
                "password_policy": {
                    "min_length": 8,
                    "require_special_chars": True,
                    "require_numbers": True,
                    "require_uppercase": True,
                },
            },
            "security": {
                "enable_rbac": True,
                "enable_audit_logging": True,
                "enable_policy_enforcement": True,
                "security_scan_enabled": True,
                "secure_delete": False,
            },
            "performance": {
                "enable_caching": True,
                "cache_ttl_seconds": 3600,
                "enable_profiling": True,
                "resource_monitoring": True,
            },
            "telemetry": {
                "enabled": True,
                "collect_usage_stats": True,
                "collect_performance_metrics": True,
                "retention_days": 90,
            },
        }
        self.save_configuration()

    def save_configuration(self) -> None:
        """Save configuration to file."""
        with self._lock:
            try:
                with open(self.config_file, "w") as f:
                    json.dump(self.config, f, indent=2)
                self.logger.info(f"Saved configuration to {self.config_file}")
            except Exception as e:
                self.logger.error(f"Failed to save configuration: {e}")

    def get_config_value(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        keys = key_path.split(".")
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set_config_value(self, key_path: str, value: Any) -> None:
        """Set configuration value using dot notation."""
        with self._lock:
            keys = key_path.split(".")
            config = self.config

            # Navigate to parent dict
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]

            # Set the value
            config[keys[-1]] = value
            self.save_configuration()


class EnterpriseManager:
    """Main enterprise features manager."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(f"{__name__}.EnterpriseManager")

        # Initialize components
        self.config_manager = ConfigurationManager()
        self.rbac = RoleBasedAccessControl()
        self.audit_logger = AuditLogger()
        self.policy_engine = PolicyEngine()

        # User management
        self.users: Dict[str, User] = {}
        self._lock = threading.RLock()

        # Current session info
        self.current_user: Optional[User] = None
        self.current_session_id: Optional[str] = None

        # Load default admin user if enabled
        if self.config_manager.get_config_value("enterprise.enabled", False):
            self._create_default_admin()

    def _create_default_admin(self) -> None:
        """Create default admin user if none exists."""
        with self._lock:
            if not self.users:
                admin_user = User(
                    user_id="admin",
                    username="admin",
                    email="admin@localhost",
                    roles={Role.ADMIN},
                    created_at=time.time(),
                )
                self.users[admin_user.user_id] = admin_user
                self.logger.info("Created default admin user")

    def create_user(
        self,
        username: str,
        email: Optional[str] = None,
        roles: Optional[Set[Role]] = None,
    ) -> User:
        """Create a new user."""
        user_id = str(uuid.uuid4())
        default_role = Role(
            self.config_manager.get_config_value("enterprise.default_user_role", "user")
        )

        user = User(
            user_id=user_id,
            username=username,
            email=email,
            roles=roles or {default_role},
            created_at=time.time(),
        )

        with self._lock:
            self.users[user_id] = user

        self.audit_logger.log_audit_entry(
            AuditLogEntry(
                action=AuditAction.USER_CREATED,
                resource=username,
                details={"user_id": user_id, "roles": [r.value for r in user.roles]},
            )
        )

        return user

    def authenticate_user(
        self, username: str, password: Optional[str] = None
    ) -> Optional[User]:
        """Authenticate user (simplified for demo)."""
        with self._lock:
            user = next(
                (u for u in self.users.values() if u.username == username), None
            )

            if user and user.active:
                user.last_login = time.time()
                self.current_user = user

                self.audit_logger.log_audit_entry(
                    AuditLogEntry(
                        user_id=user.user_id,
                        action=AuditAction.LOGIN,
                        resource=username,
                        success=True,
                    )
                )

                return user

        return None

    def check_permission(
        self, permission: Permission, resource: Optional[str] = None
    ) -> bool:
        """Check if current user has permission."""
        if not self.current_user:
            return False

        has_permission = self.rbac.user_has_permission(self.current_user, permission)

        self.audit_logger.log_permission_check(
            user_id=self.current_user.user_id,
            permission=permission,
            granted=has_permission,
            resource=resource,
        )

        return has_permission

    def evaluate_command(self, command: str) -> Dict[str, Any]:
        """Evaluate command for enterprise policies."""
        if not self.current_user:
            return {"allowed": False, "reason": "No authenticated user"}

        # Check basic permissions
        if not self.check_permission(Permission.EXECUTE_COMMAND):
            return {"allowed": False, "reason": "Insufficient permissions"}

        # Evaluate against policies
        policy_result = self.policy_engine.evaluate_command(command, self.current_user)

        return policy_result

    def get_enterprise_status(self) -> Dict[str, Any]:
        """Get enterprise features status."""
        return {
            "enabled": self.config_manager.get_config_value(
                "enterprise.enabled", False
            ),
            "current_user": self.current_user.username if self.current_user else None,
            "total_users": len(self.users),
            "rbac_enabled": self.config_manager.get_config_value(
                "security.enable_rbac", True
            ),
            "audit_enabled": self.config_manager.get_config_value(
                "security.enable_audit_logging", True
            ),
            "policies_active": len(
                [p for p in self.policy_engine.policies.values() if p.active]
            ),
        }


# Global enterprise manager
_enterprise_manager: Optional[EnterpriseManager] = None


def get_enterprise_manager() -> EnterpriseManager:
    """Get global enterprise manager instance."""
    global _enterprise_manager
    if _enterprise_manager is None:
        _enterprise_manager = EnterpriseManager()
    return _enterprise_manager
