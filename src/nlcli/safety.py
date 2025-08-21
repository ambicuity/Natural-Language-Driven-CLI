"""
Safety Layer - Guards against dangerous operations and provides security checks.
"""
import re
from pathlib import Path
from typing import List, Set

from nlcli.context import SessionContext, Intent


# Dangerous command patterns to block
DANGEROUS_PATTERNS = [
    r'rm\s+-rf\s+/',  # rm -rf /
    r'rm\s+-rf\s+\*',  # rm -rf *
    r':\(\)\{\s*:\|:\s*&\s*\}',  # fork bomb
    r'dd\s+if=.*of=/dev/',  # dd to device
    r'mkfs\.',  # format filesystem
    r'fdisk',  # disk partitioning
    r'chmod\s+-R\s+777',  # recursive 777 permissions
    r'chown\s+-R.*root',  # change ownership to root
    r'sudo\s+rm',  # sudo rm anything
    r'curl.*\|\s*sh',  # curl | sh
    r'wget.*\|\s*sh',  # wget | sh
]

# Suspicious command patterns that require extra confirmation
SUSPICIOUS_PATTERNS = [
    r'rm\s+.*\*',  # rm with wildcards
    r'mv\s+.*\*',  # mv with wildcards  
    r'cp\s+.*\*',  # cp with wildcards
    r'chmod\s+.*\*',  # chmod with wildcards
    r'find.*-exec\s+rm',  # find with rm execution
    r'find.*-delete',  # find with delete
    r'>\s*/dev/',  # redirect to device
    r'2>&1',  # error redirection
]

# Required tools/commands that should always be available
REQUIRED_TOOLS = {"find", "ls", "grep", "du", "stat"}

# Allowed command prefixes (whitelist approach)
ALLOWED_COMMANDS = {
    "find", "ls", "grep", "du", "stat", "cat", "head", "tail", "wc", "sort", "uniq",
    "awk", "sed", "cut", "tr", "xargs", "file", "which", "whereis", "pwd", "whoami",
    "date", "uptime", "df", "ps", "top", "netstat", "ss", "ping", "curl", "wget",
    "git", "pip", "python", "python3", "node", "npm", "lsof", "kill", "pkill", "pstree", 
    "free", "dig", "ip", "ifconfig", "brew", "apt", "apt-get", "apt-cache"
}


class SafetyGuard:
    """Safety guard for validating commands before execution."""
    
    def __init__(self):
        self.allowed_directories: Set[str] = set()
        self.blocked_patterns = DANGEROUS_PATTERNS
        self.suspicious_patterns = SUSPICIOUS_PATTERNS
    
    def add_allowed_directory(self, path: str) -> None:
        """Add a directory to the allowed list."""
        self.allowed_directories.add(str(Path(path).resolve()))
    
    def is_command_safe(self, intent: Intent, context: SessionContext) -> tuple[bool, str]:
        """
        Check if a command is safe to execute.
        
        Args:
            intent: Intent object with command details
            context: Session context
            
        Returns:
            Tuple of (is_safe, reason)
        """
        command = intent.command
        
        # Check for dangerous patterns
        for pattern in self.blocked_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"Command contains dangerous pattern: {pattern}"
        
        # Check command whitelist
        first_word = command.split()[0] if command.split() else ""
        if first_word not in ALLOWED_COMMANDS:
            return False, f"Command '{first_word}' is not in the allowed list"
        
        # Check path safety
        if not self._are_paths_safe(intent, context):
            return False, "Command operates on restricted paths"
        
        # Check for shell injection patterns
        if self._has_shell_injection(command):
            return False, "Command contains potential shell injection"
        
        return True, "Command appears safe"
    
    def requires_confirmation(self, intent: Intent) -> tuple[bool, str]:
        """
        Check if command requires user confirmation.
        
        Args:
            intent: Intent object
            
        Returns:
            Tuple of (requires_confirmation, reason)
        """
        command = intent.command
        
        # Always confirm destructive operations
        if intent.danger_level in ("destructive", "modify"):
            return True, f"Destructive operation ({intent.danger_level})"
        
        # Check for suspicious patterns
        for pattern in self.suspicious_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return True, f"Suspicious pattern detected: {pattern}"
        
        # Check for operations on many files
        if re.search(r'\*.*\*', command):  # Multiple wildcards
            return True, "Multiple wildcards detected"
        
        # Check for system directories
        system_dirs = ["/etc", "/usr", "/var", "/sys", "/proc", "/boot"]
        for sys_dir in system_dirs:
            if sys_dir in command:
                return True, f"Operation on system directory: {sys_dir}"
        
        return False, ""
    
    def get_undo_hint(self, intent: Intent) -> str:
        """
        Provide undo hints for reversible operations.
        
        Args:
            intent: Intent object
            
        Returns:
            Hint string for undoing the operation
        """
        command = intent.command
        
        if "mv " in command and intent.danger_level == "modify":
            return "Use 'mv' command in reverse to undo file moves"
        
        if "cp " in command:
            return "Delete copied files to undo"
        
        if intent.tool_name == "find_files" and intent.danger_level == "destructive":
            return "Files moved to ~/.nlcli_trash - use 'restore' command to recover"
        
        return "This operation may not be easily reversible"
    
    def _are_paths_safe(self, intent: Intent, context: SessionContext) -> bool:
        """Check if all paths in the command are within allowed directories."""
        # Extract paths from arguments (skip URL arguments)
        paths_to_check = []
        
        if "path" in intent.args and intent.args["path"] not in [".", "./"]:
            paths_to_check.append(intent.args["path"])
        
        # Don't check URLs as paths
        if intent.tool_name in ["http_request", "download_file"]:
            return True  # URLs are not filesystem paths
        
        # Also check for paths in the raw command (but skip URLs)
        if not intent.command.startswith("curl") and not intent.command.startswith("wget"):
            command_paths = re.findall(r'([~/][^\s]+)', intent.command)
            paths_to_check.extend(command_paths)
        
        for path_str in paths_to_check:
            try:
                # Skip URLs
                if path_str.startswith(("http://", "https://", "ftp://")):
                    continue
                    
                # Resolve path
                if path_str.startswith("~"):
                    path = Path.home() / path_str[2:]
                else:
                    path = Path(path_str).resolve()
                
                # Check if path is allowed
                if not context.is_path_allowed(path):
                    return False
                    
            except Exception:
                # If we can't resolve the path, err on the side of caution
                return False
        
        return True
    
    def _has_shell_injection(self, command: str) -> bool:
        """Check for potential shell injection patterns."""
        injection_patterns = [
            r';.*rm',  # Command chaining with rm
            r'&&.*rm',  # Command chaining with rm
            r'\|.*sh',  # Pipe to shell
            r'\$\(',  # Command substitution
            r'`',  # Backticks
            r'eval\s+',  # eval command
            r'exec\s+',  # exec command
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return True
        
        return False


# Global safety guard instance
_safety_guard = SafetyGuard()


def guard(intent: Intent, context: SessionContext) -> bool:
    """
    Main safety check function.
    
    Args:
        intent: Intent object to check
        context: Session context
        
    Returns:
        True if command is safe to execute, False otherwise
    """
    if not intent:
        return False
    
    is_safe, reason = _safety_guard.is_command_safe(intent, context)
    
    if not is_safe:
        print(f"🚫 Safety check failed: {reason}")
        return False
    
    return True


def requires_confirmation(intent: Intent) -> bool:
    """Check if command requires user confirmation."""
    needs_confirmation, reason = _safety_guard.requires_confirmation(intent)
    return needs_confirmation


def get_undo_hint(intent: Intent) -> str:
    """Get undo hint for an operation."""
    return _safety_guard.get_undo_hint(intent)


def configure_safety(allowed_dirs: List[str]) -> None:
    """Configure safety settings."""
    for directory in allowed_dirs:
        _safety_guard.add_allowed_directory(directory)