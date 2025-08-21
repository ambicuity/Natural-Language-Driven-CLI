# Installation Guide

## Quick Installation

### From PyPI (Recommended)
```bash
pip install nlcli
```

### From Source
```bash
git clone https://github.com/ambicuity/Natural-Language-Driven-CLI.git
cd Natural-Language-Driven-CLI
pip install -e .
```

## System Requirements

- Python 3.10 or higher
- Works on Linux, macOS, and Windows
- No additional dependencies required for basic functionality

## Optional Dependencies

### Local LLM Support
```bash
pip install nlcli[llm]
```

### Development Tools
```bash
pip install nlcli[dev]
```

## Verification

Test your installation:
```bash
nlcli --help
nlcli
```

You should see the welcome message and interactive prompt.

## Troubleshooting

### Permission Issues
If you get permission errors, try:
```bash
pip install --user nlcli
```

### Path Issues
Make sure `~/.local/bin` is in your PATH:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Windows Users
On Windows, you might need to add the Scripts directory to your PATH:
```
%APPDATA%\Python\PythonXX\Scripts
```