# Natural Language Driven CLI

A cross-platform command-line tool that turns natural language into safe, auditable system commands.

**🔥 Turn your thoughts into commands, safely and intuitively.**

```bash
› show files >1GB modified this week
› find all .py files containing TODO  
› list processes using port 3000
```

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI (recommended)
pip install nlcli

# Or install from source
git clone https://github.com/ambicuity/Natural-Language-Driven-CLI.git
cd Natural-Language-Driven-CLI
pip install -e .
```

### First Run

```bash
# Start the interactive CLI
nlcli

# Try these examples
› show files >500MB
› find processes using port 8080
› list installed packages
› ping google.com
```

That's it! The CLI will safely show you what commands it would run before executing them.

## 🌟 Key Features

### 🛡️ Safety First
- **Dry-run by default** - See what commands will do before execution
- **Smart confirmations** - Required for destructive operations  
- **Sandboxed execution** - Commands run with timeouts and resource limits
- **Path restrictions** - Operations limited to allowed directories

### 🧠 Smart Understanding
- **Natural language** - Just describe what you want to do
- **Context awareness** - Remembers your session state
- **Multi-step operations** - Chain commands together
- **Multi-language support** - Works in Spanish, French, German, and more

### 🔧 Built-in Tools
- **File operations** - find, search, disk usage, file info
- **Process management** - list, kill by port/name, system resources
- **Network tools** - ping, curl, DNS lookup, download files
- **Package info** - brew/apt package details and search
- **Git operations** - status, log, diff, branches (read-only)

## 📖 Usage Examples

### File Operations
```bash
› what's taking up space in Downloads
› find .log files modified today
› search for "error" in config files
```

### Process Management
```bash
› show top 5 CPU processes
› list processes using port 3000
› kill chrome processes
```

### Network & System
```bash
› ping google.com
› check listening ports  
› download file from https://example.com/data.zip
```

### Package Management
```bash
› search python packages
› show info for package curl
› list installed homebrew packages
```

## ⚙️ Configuration

Optional configuration file: `~/.nlcli/config.json`

```json
{
  "preferences": {
    "confirm_by_default": true,
    "language": "en",
    "max_results": 50
  },
  "safety": {
    "timeout_seconds": 30,
    "allowed_directories": ["/Users/username", "/tmp"]
  }
}
```

## 🛡️ Safety & Security

Built-in protections keep your system safe:

- ✅ **Whitelist approach** - Only known-safe commands allowed
- ✅ **Dangerous patterns blocked** - `rm -rf /`, `chmod 777 *`, etc.
- ✅ **Confirmation prompts** - Destructive operations require approval
- ✅ **Resource limits** - Commands have timeouts and output limits
- ✅ **Audit logging** - All operations logged for review

## 🔌 Advanced Features

### Batch Mode
```bash
# Execute multiple commands
nlcli --batch-commands "find large files" --batch-commands "show disk usage"

# Run from script
nlcli --batch script.nlcli
```

### Plugin System
Create custom tools by adding Python files to `~/.nlcli/plugins/`. See [docs/PLUGIN_DEVELOPMENT.md](docs/PLUGIN_DEVELOPMENT.md) for details.

### Multi-language Support
```bash
› mostrar archivos grandes     # Spanish
› lister tous les fichiers     # French  
› alle dateien anzeigen        # German
```

## 🧪 Development

```bash
git clone https://github.com/ambicuity/Natural-Language-Driven-CLI.git
cd Natural-Language-Driven-CLI
pip install -e ".[dev]"

# Run tests
pytest tests/

# Code formatting
black src/ tests/
isort src/ tests/
```

## 📚 Documentation

- [Installation Guide](docs/INSTALLATION.md)
- [Configuration Reference](docs/CONFIGURATION.md)
- [Plugin Development](docs/PLUGIN_DEVELOPMENT.md)
- [Security Features](docs/SECURITY.md)
- [Advanced Usage](docs/ADVANCED_USAGE.md)
- [Real World Examples](examples/)

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📜 License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.

---

**Need help?** Type `help` in the CLI or check our [documentation](docs/).