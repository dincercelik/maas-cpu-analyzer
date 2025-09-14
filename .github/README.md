# GitHub Actions Workflows

This directory contains GitHub Actions workflows for the MAAS CPU Analyzer project.

## Workflows

### 1. CI/CD Pipeline (`ci.yml`)
**Triggers:** Push to main/develop, Pull requests to main/develop

**Jobs:**
- **Test Suite**: Runs tests on Python 3.9, 3.10, 3.11, 3.12
- **Code Quality**: Runs linting, type checking, and formatting checks
- **Security Scan**: Runs security vulnerability checks
- **Build Package**: Builds and validates the Python package
- **Release**: Publishes to PyPI (only on main branch pushes)

### 2. Pull Request Checks (`pr.yml`)
**Triggers:** Pull requests to main/develop

**Jobs:**
- **PR Quality Checks**: Comprehensive quality checks including:
  - Unit and integration tests
  - Linting and type checking
  - Formatting validation
  - Security checks
  - TODO/FIXME comment detection
  - Debug print statement detection
- **Test Coverage**: Generates and uploads coverage reports
- **Dependency Security Check**: Checks for security vulnerabilities

### 3. Release (`release.yml`)
**Triggers:** Git tags (v*), Manual dispatch

**Jobs:**
- **Test Before Release**: Runs full test suite on all Python versions
- **Build and Release**:
  - Builds the package
  - Publishes to PyPI
  - Creates GitHub release with assets

### 4. Dependency Updates (`dependency-update.yml`)
**Triggers:** Weekly schedule (Mondays), Manual dispatch

**Jobs:**
- **Check for Dependency Updates**:
  - Identifies outdated packages
  - Generates dependency tree
  - Runs security checks
- **Test with Updated Dependencies**:
  - Updates dependencies
  - Runs tests
  - Creates PR with updates (manual trigger only)

### 5. CodeQL Analysis (`codeql.yml`)
**Triggers:** Push to main/develop, Pull requests to main, Daily schedule

**Jobs:**
- **Analyze**: Runs GitHub's CodeQL security analysis

### 6. Status Check (`status.yml`)
**Triggers:** Completion of CI/CD Pipeline or PR Checks

**Jobs:**
- **Check Workflow Status**: Monitors workflow completion status

## Configuration Files

### Dependabot (`dependabot.yml`)
- Automatically creates PRs for dependency updates
- Updates pip dependencies weekly
- Updates GitHub Actions weekly

### Issue Templates
- **Bug Report**: Structured template for bug reports
- **Feature Request**: Template for feature requests

### Pull Request Template
- Comprehensive checklist for PR submissions
- Ensures code quality and testing standards

## Usage

### Local Development
```bash
# Run tests locally
make test
# or
tox

# Run specific checks
make lint
make format
make security

# Run with coverage
make test-coverage
```

### CI/CD Integration
The workflows automatically run on:
- **Push to main/develop**: Full CI/CD pipeline
- **Pull requests**: Quality checks and tests
- **Git tags**: Release process
- **Weekly schedule**: Dependency updates and security scans

### Secrets Required
For full functionality, add these secrets to your repository:
- `PYPI_API_TOKEN`: PyPI API token for publishing packages

## Workflow Status Badges

Add these badges to your README.md:

```markdown
![CI/CD Pipeline](https://github.com/dincercelik/maas-cpu-analyzer/workflows/CI/CD%20Pipeline/badge.svg)
![Pull Request Checks](https://github.com/dincercelik/maas-cpu-analyzer/workflows/Pull%20Request%20Checks/badge.svg)
![CodeQL](https://github.com/dincercelik/maas-cpu-analyzer/workflows/CodeQL/badge.svg)
```

## Benefits

1. **Automated Testing**: Ensures code quality across multiple Python versions
2. **Security Scanning**: Regular vulnerability checks and CodeQL analysis
3. **Dependency Management**: Automated updates and security monitoring
4. **Release Automation**: Streamlined package publishing process
5. **Code Quality**: Enforced linting, formatting, and type checking
6. **Coverage Tracking**: Monitors test coverage and reports to Codecov
7. **Documentation**: Automated documentation building and validation
