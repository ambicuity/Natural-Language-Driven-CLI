# Contributing to Natural Language Driven CLI

We welcome contributions to make NLCLI better! Here's how you can help.

## Quick Start

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Add tests for your changes
5. Run tests: `pytest tests/`
6. Submit a pull request

## Development Setup

```bash
git clone https://github.com/ambicuity/Natural-Language-Driven-CLI.git
cd Natural-Language-Driven-CLI
pip install -e ".[dev]"
```

## Code Quality

We use several tools to maintain code quality:

```bash
# Format code
black src/ tests/

# Sort imports  
isort src/ tests/

# Lint
flake8 src/ tests/

# Type checking
mypy src/

# Run all tests
pytest tests/
```

## Areas We Need Help With

- **Tool implementations**: Add support for more system tools
- **Language support**: Add more languages for natural language input
- **Documentation**: Improve guides and examples
- **Testing**: Add more test coverage
- **Plugin ecosystem**: Create plugins for specialized domains

## Submitting Changes

1. Make sure tests pass
2. Update documentation if needed
3. Add tests for new functionality
4. Write clear commit messages
5. Submit a pull request with description of changes

## Reporting Issues

- Use GitHub Issues for bug reports
- Include steps to reproduce the issue
- Provide system information (OS, Python version)
- Check existing issues first

## Security Issues

For security vulnerabilities, please email security@nlcli.org instead of creating a public issue.

## Code of Conduct

Be respectful and inclusive. We want this project to be welcoming to everyone.

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.