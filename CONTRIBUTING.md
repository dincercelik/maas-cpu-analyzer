# Contributing to MAAS CPU Analyzer

Thank you for your interest in contributing to MAAS CPU Analyzer! This document provides guidelines and information for contributors.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/dincercelik/maas-cpu-analyzer.git`
3. Create a virtual environment: `python3 -m venv .venv`
4. Activate the virtual environment: `source .venv/bin/activate`
5. Install the package in development mode: `pip install -e .`

## Development Setup

### Prerequisites
- Python 3.9+
- MAAS 3.5+ (for testing)
- OpenStack 2024.1+ (for testing trait creation)

### Project Structure
```
maas-cpu-analyzer/
├── maas_cpu_analyzer/         # Main package directory
│   ├── __init__.py            # Package initialization
│   └── maas_cpu_analyzer.py   # Main application logic
├── setup.py                   # Setup script
├── setup.cfg                  # Package configuration
├── pyproject.toml             # Modern build configuration
├── requirements.txt           # Dependencies
├── README.md                  # Project documentation
├── CONTRIBUTING.md            # This file
├── LICENSE                    # MIT license
└── MANIFEST.in                # Package manifest
```

### Environment Variables
Set up the following environment variables for testing:
```bash
export MAAS_URL="http://your-maas-server:5240/MAAS"
export MAAS_API_KEY="your-maas-api-key"
export OS_AUTH_URL="http://your-openstack:5000/v3"
export OS_USERNAME="your-username"
export OS_PASSWORD="your-password"
export OS_PROJECT_NAME="your-project"
```

## Making Changes

1. Create a new branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Test your changes thoroughly
4. Update documentation if needed
5. Commit your changes: `git commit -m "Add your feature"`
6. Push to your fork: `git push origin feature/your-feature-name`
7. Create a Pull Request

## Code Style

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Add docstrings for functions and classes
- Keep functions focused and small
- Use meaningful variable and function names

## Testing

Before submitting a PR, please test your changes:

1. Test the command-line tool: `maas-cpu-analyzer --help`
2. Test with different MAAS zones
3. Test with various tag combinations
4. Test trait creation functionality
5. Test error handling scenarios
6. Verify help text and documentation
7. Test package building: `python -m build`
8. Test package validation: `twine check dist/*`

## Pull Request Guidelines

- Provide a clear description of your changes
- Reference any related issues
- Include test results
- Update documentation if needed
- Ensure all tests pass

## Reporting Issues

When reporting issues, please include:

- MAAS version
- OpenStack version
- Python version
- Error messages and logs
- Steps to reproduce
- Expected vs actual behavior

## License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.
