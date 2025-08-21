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

### Legacy Dependency Issues
If you encounter build errors related to `fann2` or `padatious` dependencies, this was an issue with older PyPI versions (≤ 0.1.2). These dependencies have been removed in version 0.1.3 and later.

To fix this:
```bash
# Clear pip cache and upgrade
pip cache purge
pip install --upgrade --no-cache-dir nlcli

# If still having issues, install from source
git clone https://github.com/ambicuity/Natural-Language-Driven-CLI.git
cd Natural-Language-Driven-CLI
pip install -e .
```