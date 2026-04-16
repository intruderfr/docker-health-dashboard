# Contributing to Docker Health Dashboard

We welcome contributions from the community! Here's how you can help.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/docker-health-dashboard.git`
3. Create a virtual environment: `python -m venv venv`
4. Activate it: `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
5. Install development dependencies: `pip install -e ".[dev]"`

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=docker_health_dashboard --cov-report=html

# Run specific test file
pytest tests/test_models.py -v
```

### Code Quality

```bash
# Format code
black docker_health_dashboard/ tests/

# Run linter
flake8 docker_health_dashboard/

# Type checking
mypy docker_health_dashboard/

# Sort imports
isort docker_health_dashboard/ tests/
```

### Running Locally

CLI:
```bash
docker-health-dashboard status
docker-health-dashboard monitor
```

Web Dashboard:
```bash
python -m docker_health_dashboard.web
# Then visit http://localhost:8080
```

## Commit Guidelines

- Use clear, descriptive commit messages
- Reference issues in commit messages: `git commit -m "Fix issue #123"`
- Keep commits atomic and focused

## Pull Request Process

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Add tests for new functionality
4. Ensure all tests pass: `pytest tests/ -v`
5. Ensure code quality checks pass: `black`, `flake8`, `mypy`
6. Push to your fork
7. Create a Pull Request with a clear description

## Report Bugs

Use GitHub Issues to report bugs. Include:
- Clear description of the issue
- Steps to reproduce
- Expected behavior
- Actual behavior
- Your environment (Python version, Docker version, OS)

## Suggest Features

Have an idea? Open an issue with:
- Clear description of the feature
- Use cases and benefits
- Potential implementation approach (optional)

## Code of Conduct

Be respectful and inclusive. We're all here to learn and improve the project together.

## Questions?

Feel free to open an issue or reach out to the maintainers.

Thank you for contributing!
