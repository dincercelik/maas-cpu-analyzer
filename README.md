# MAAS CPU Analyzer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![MAAS 3.5+](https://img.shields.io/badge/MAAS-3.5+-green.svg)](https://maas.io/)
[![OpenStack 2024.1+](https://img.shields.io/badge/OpenStack-2024.1+-orange.svg)](https://www.openstack.org/)
[![CI/CD Pipeline](https://github.com/dincercelik/maas-cpu-analyzer/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/dincercelik/maas-cpu-analyzer/actions)
[![Pull Request Checks](https://github.com/dincercelik/maas-cpu-analyzer/workflows/Pull%20Request%20Checks/badge.svg)](https://github.com/dincercelik/maas-cpu-analyzer/actions)
[![CodeQL](https://github.com/dincercelik/maas-cpu-analyzer/workflows/CodeQL/badge.svg)](https://github.com/dincercelik/maas-cpu-analyzer/actions)

A Python tool to analyze CPU models in MAAS (Metal as a Service) machines and optionally create corresponding OpenStack traits for resource scheduling and placement optimization.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Environment Variables](#environment-variables)
- [Dependencies](#dependencies)
- [Examples](#examples)
- [Development](#development)
- [CI/CD](#cicd)
- [Contributing](#contributing)
- [License](#license)

## Features

- List CPU models from MAAS machines by zone
- Filter by deployment status (deployed only or all machines)
- Filter by MAAS tags
- Generate and create OpenStack traits from CPU models
- Verbose logging for debugging

## Requirements

- **Python**: 3.9 or higher
- **MAAS**: 3.5 or higher
- **OpenStack**: 2024.1 or higher (for trait creation)
- **Network Access**: To MAAS and OpenStack APIs

## Installation

### Install from PyPI (Recommended)
```bash
pip install maas-cpu-analyzer
```

### Install from Source
```bash
# Clone the repository
git clone https://github.com/dincercelik/maas-cpu-analyzer.git
cd maas-cpu-analyzer

# Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Note**: The requirements are pinned for compatibility with MAAS 3.5+ and OpenStack 2024.1+.

### Set up Environment Variables
```bash
# Required for all operations:
export MAAS_URL="http://your-maas-server:5240/MAAS"
export MAAS_API_KEY="your-maas-api-key"

# Required only for OpenStack operations (--create-os-traits):
export OS_AUTH_URL="http://your-openstack:5000/v3"
export OS_USERNAME="your-username"
export OS_PASSWORD="your-password"
export OS_PROJECT_NAME="your-project"
```

## Usage

### Basic Usage
```bash
# Activate virtual environment
source .venv/bin/activate

# Show all machines in all zones
maas-cpu-analyzer

# Show all machines in a specific zone
maas-cpu-analyzer --zone zone-1

# Show only deployed machines in a zone
maas-cpu-analyzer --zone zone-1 --deployed-only

# Filter by tags in specific zone
maas-cpu-analyzer --zone zone-1 --tags compute,gpu

# Show deployed machines with specific tags in a zone
maas-cpu-analyzer --zone zone-1 --deployed-only --tags compute

# Create OpenStack traits
maas-cpu-analyzer --zone zone-1 --create-os-traits

# Verbose output
maas-cpu-analyzer --verbose

# Show help
maas-cpu-analyzer --help
```

## Environment Variables

### Required for all operations
- `MAAS_URL`: MAAS server URL
- `MAAS_API_KEY`: MAAS API key for authentication

### Required only for OpenStack operations (--create-os-traits)
- `OS_AUTH_URL`: OpenStack authentication URL
- `OS_USERNAME`: OpenStack username
- `OS_PASSWORD`: OpenStack password
- `OS_PROJECT_NAME`: OpenStack project name

## Dependencies

- Python 3.9+
- requests>=2.31.0,<3.0.0 (for HTTP requests)
- requests-oauthlib>=1.3.1,<2.0.0 (for MAAS OAuth 1.0a authentication)
- openstacksdk>=4.7.0,<5.0.0 (for OpenStack operations)

### Version Compatibility
- **MAAS**: 3.5+
- **OpenStack**: 2024.1+

## Examples

### Basic Analysis
```bash
# Show all machines in all zones
maas-cpu-analyzer

# Show all machines in a specific zone
maas-cpu-analyzer --zone zone-1

# Show only deployed machines in a zone
maas-cpu-analyzer --zone zone-1 --deployed-only
```

### Filtering by Tags
```bash
# Show compute nodes in specific zone
maas-cpu-analyzer --zone zone-1 --tags compute

# Show compute or GPU nodes in specific zone
maas-cpu-analyzer --zone zone-1 --tags compute,gpu

# Show deployed compute nodes in specific zone
maas-cpu-analyzer --zone zone-1 --deployed-only --tags compute
```

### Creating OpenStack Traits
```bash
# Create traits for all machines in a zone
maas-cpu-analyzer --zone zone-1 --create-os-traits

# Create traits for specific tag groups in a zone
maas-cpu-analyzer --zone zone-1 --tags compute --create-os-traits
```

### Debugging
```bash
# Enable verbose output for troubleshooting
maas-cpu-analyzer --zone zone-1 --create-os-traits --verbose
```

## Development

### Setup Development Environment
```bash
# Clone the repository
git clone https://github.com/dincercelik/maas-cpu-analyzer.git
cd maas-cpu-analyzer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

### Running Tests
```bash
# Run all tests
make test
# or
tox

# Run specific test environments
make lint          # Code linting
make format        # Code formatting
make security      # Security checks
make test-coverage # Tests with coverage

# Run individual test suites
pytest tests/unit/                    # Unit tests only
pytest tests/integration/             # Integration tests only
pytest --cov=maas_cpu_analyzer        # With coverage
```

### Code Quality
```bash
# Format code
make format

# Check formatting
make format-check

# Run linting
make lint

# Run type checking
make type-check

# Run security checks
make security
```

## CI/CD

This project uses GitHub Actions for continuous integration and deployment:

### Workflows
- **CI/CD Pipeline**: Runs on push to main/develop and PRs
- **Pull Request Checks**: Comprehensive quality checks for PRs
- **Release**: Automated package publishing to PyPI
- **Dependency Updates**: Weekly dependency updates and security scans
- **CodeQL**: Security analysis and vulnerability detection

### Features
- ✅ Multi-Python version testing (3.9, 3.10, 3.11, 3.12)
- ✅ Automated testing with pytest and tox
- ✅ Code quality checks (linting, formatting, type checking)
- ✅ Security scanning (bandit, safety, CodeQL)
- ✅ Coverage reporting with Codecov
- ✅ Automated dependency updates
- ✅ Package building and PyPI publishing
- ✅ Documentation building

### Status Badges
The project includes status badges showing:
- CI/CD Pipeline status
- Pull Request Checks status
- CodeQL security analysis status

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
