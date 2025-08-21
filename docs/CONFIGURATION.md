# Configuration Reference

NLCLI can be configured through a JSON file located at `~/.nlcli/config.json`.

## Default Configuration

If no configuration file exists, NLCLI uses these defaults:

```json
{
  "preferences": {
    "default_editor": "nano",
    "confirm_by_default": true,
    "allowed_directories": [],
    "model_preference": "local",
    "language": "en",
    "max_results": 50,
    "trash_instead_of_delete": true
  },
  "safety": {
    "timeout_seconds": 30,
    "max_output_size": "1MB"
  }
}
```

## Configuration Options

### Preferences

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `default_editor` | string | `"nano"` | Default text editor for file editing |
| `confirm_by_default` | boolean | `true` | Require confirmation for destructive operations |
| `allowed_directories` | array | `[]` | List of directories where operations are allowed (empty = all user directories) |
| `model_preference` | string | `"local"` | Preferred LLM model (`"local"`, `"cloud"`, `"auto"`) |
| `language` | string | `"en"` | Default language for natural language input |
| `max_results` | number | `50` | Maximum number of results to display |
| `trash_instead_of_delete` | boolean | `true` | Move files to trash instead of permanent deletion |

### Safety Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `timeout_seconds` | number | `30` | Maximum time to wait for command execution |
| `max_output_size` | string | `"1MB"` | Maximum size of command output to display |

### Enterprise Configuration

For enterprise deployments, additional options are available:

```json
{
  "enterprise": {
    "enabled": false,
    "organization": "Default Organization",
    "audit_retention_days": 365,
    "require_user_authentication": false,
    "default_user_role": "user",
    "session_timeout_minutes": 60
  },
  "security": {
    "enable_rbac": true,
    "enable_audit_logging": true,
    "enable_policy_enforcement": true,
    "security_scan_enabled": true
  },
  "performance": {
    "enable_caching": true,
    "cache_ttl_seconds": 3600,
    "enable_profiling": true,
    "resource_monitoring": true
  },
  "telemetry": {
    "enabled": true,
    "collect_usage_stats": true,
    "collect_performance_metrics": true,
    "retention_days": 90
  }
}
```

## Environment Variables

You can also configure NLCLI using environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `NLCLI_CONFIG_PATH` | Path to configuration file | `/custom/path/config.json` |
| `NLCLI_DEFAULT_LANG` | Default language | `es`, `fr`, `de` |
| `NLCLI_LLM_ENABLED` | Enable local LLM integration | `true`, `false` |
| `NLCLI_CLOUD_LLM_ENABLED` | Enable cloud LLM fallback | `true`, `false` |
| `OPENAI_API_KEY` | OpenAI API key for cloud LLM | `sk-...` |
| `ANTHROPIC_API_KEY` | Anthropic API key | `sk-ant-...` |
| `GOOGLE_API_KEY` | Google API key | `AIza...` |

## Configuration Commands

### View Current Configuration
```bash
› config              # Show current configuration
› config get safety   # Show specific section
```

### Update Configuration
```bash
› config set preferences.language es
› config set safety.timeout_seconds 60
```

### Reset Configuration
```bash
› config reset        # Reset to defaults
› config backup       # Backup current configuration
```

## Examples

### Basic User Configuration
```json
{
  "preferences": {
    "language": "es",
    "max_results": 20,
    "confirm_by_default": true
  },
  "safety": {
    "timeout_seconds": 45,
    "allowed_directories": ["/Users/myname", "/tmp"]
  }
}
```

### Power User Configuration
```json
{
  "preferences": {
    "default_editor": "vim",
    "confirm_by_default": false,
    "model_preference": "cloud",
    "max_results": 100
  },
  "safety": {
    "timeout_seconds": 60,
    "max_output_size": "5MB"
  }
}
```

### Enterprise Configuration
```json
{
  "enterprise": {
    "enabled": true,
    "organization": "ACME Corp",
    "audit_retention_days": 2555,
    "require_user_authentication": true
  },
  "security": {
    "enable_rbac": true,
    "enable_audit_logging": true,
    "security_scan_enabled": true
  },
  "preferences": {
    "confirm_by_default": true,
    "allowed_directories": ["/home/users", "/tmp", "/opt/projects"]
  }
}
```