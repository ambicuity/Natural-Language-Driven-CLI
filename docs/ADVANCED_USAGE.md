# Advanced Usage

## Architecture Overview

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

## Production Ready Features

### Security Monitoring
```bash
› security             # Show security audit report  
› security scan        # Run comprehensive security scan
```

### Performance Monitoring
```bash
› performance          # Show performance metrics
› profile              # Show performance profiling data
› monitor              # Show real-time resource monitoring
› cache stats          # Show cache performance statistics
```

### Enterprise Features
```bash
› enterprise           # Show enterprise features status
› audit                # Show audit trail
› policies             # Show security policies
› users                # Show user management (admin only)
```

## Cloud LLM Integration

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

## Batch Mode & Scripting

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

## Context Management

### Basic Context
```bash
› context              # Show basic context
› context clear        # Clear current context
```

### Advanced Context
```bash
› context advanced     # Show advanced context analysis
› context save         # Save current session context
› context load         # Load previous session context
```

## Advanced Commands

```bash
› debug on/off         # Enable/disable debug mode
› reload plugins       # Reload all plugins
› lang status          # Show language support status
› cloud status         # Show cloud LLM provider status
```

## Roadmap

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

### Phase 4 - Production Ready ✅
- [x] Comprehensive security audit
- [x] Performance optimization
- [x] Advanced error recovery
- [x] Telemetry and metrics
- [x] Enterprise features