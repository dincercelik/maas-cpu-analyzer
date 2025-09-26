# Publishing MAAS CPU Analyzer to PyPI

This guide will help you publish the MAAS CPU Analyzer package to PyPI.org.

## Prerequisites

1. **PyPI Account**: Create an account at [pypi.org](https://pypi.org) if you don't have one
2. **TestPyPI Account**: Create an account at [test.pypi.org](https://test.pypi.org) for testing
3. **API Tokens**: Generate API tokens for both PyPI and TestPyPI

## Step 1: Generate API Tokens

1. Go to [pypi.org/manage/account/](https://pypi.org/manage/account/)
2. Scroll down to "API tokens" section
3. Click "Add API token"
4. Give it a name (e.g., "maas-cpu-analyzer")
5. Set scope to "Entire account" (for first upload) or specific project
6. Copy the token (starts with `pypi-`)
7. Repeat for TestPyPI at [test.pypi.org/manage/account/](https://test.pypi.org/manage/account/)

## Step 2: Configure Credentials

Create a `.pypirc` file in your home directory:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_PYPI_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TESTPYPI_TOKEN_HERE
```

## Step 3: Test Upload to TestPyPI

First, test your package on TestPyPI:

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Build the package
python -m build

# Check the package
twine check dist/*

# Upload to TestPyPI
twine upload --repository testpypi dist/*
```

## Step 4: Test Installation from TestPyPI

Test that your package can be installed from TestPyPI:

```bash
# Create a new virtual environment for testing
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ maas-cpu-analyzer

# Test the command
maas-cpu-analyzer --help
```

## Step 5: Upload to PyPI

Once you're satisfied with the TestPyPI version:

```bash
# Upload to PyPI
twine upload dist/*
```

## Step 6: Verify Installation

Test installation from PyPI:

```bash
# Create a new virtual environment
python -m venv prod_test
source prod_test/bin/activate  # On Windows: prod_test\Scripts\activate

# Install from PyPI
pip install maas-cpu-analyzer

# Test the command
maas-cpu-analyzer --help
```

## Important Notes

### Before Publishing

1. **Update Email**: Email is already set to `hello@dincercelik.com` in:
   - `setup.cfg`
   - `pyproject.toml`

2. **Version Management**:
   - Update version in `setup.cfg` and `pyproject.toml` for new releases
   - Use semantic versioning (e.g., 1.0.1, 1.1.0, 2.0.0)

3. **Git Tags**: Create a git tag for the release:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

### Package Information

- **Package Name**: `maas-cpu-analyzer`
- **Current Version**: 1.0.0
- **Python Requirements**: >=3.8
- **Dependencies**: requests, requests-oauthlib, openstacksdk

### Files Included

The package includes:
- `maas_cpu_analyzer.py` - Main module
- `README.md` - Documentation
- `LICENSE` - MIT License
- `CONTRIBUTING.md` - Contribution guidelines
- `requirements.txt` - Dependencies
- `setup.py` and `setup.cfg` - Package configuration
- `pyproject.toml` - Modern Python packaging
- `MANIFEST.in` - File inclusion rules

## Troubleshooting

### Common Issues

1. **Package already exists**: PyPI package names must be unique. If `maas-cpu-analyzer` is taken, you'll need to choose a different name.

2. **Version already exists**: You cannot upload the same version twice. Increment the version number.

3. **Missing files**: Check that `MANIFEST.in` includes all necessary files.

4. **Build errors**: Ensure all dependencies are properly specified in `requirements.txt` and `pyproject.toml`.

### Useful Commands

```bash
# Check package contents
tar -tzf dist/maas_cpu_analyzer-1.0.0.tar.gz

# Check wheel contents
unzip -l dist/maas_cpu_analyzer-1.0.0-py3-none-any.whl

# Validate package
twine check dist/*

# View package info
python -m pip show maas-cpu-analyzer
```

## Post-Publication

After successful publication:

1. **Update README**: Add installation instructions:
   ```bash
   pip install maas-cpu-analyzer
   ```

2. **Create GitHub Release**: Tag the release in GitHub with release notes

3. **Update Documentation**: Update any external documentation to reference PyPI installation

4. **Monitor**: Check PyPI project page for any issues or user feedback

## Security

- Never commit API tokens to version control
- Use `.pypirc` file with proper permissions (600)
- Consider using environment variables for CI/CD:
  ```bash
  export TWINE_USERNAME=__token__
  export TWINE_PASSWORD=pypi-YOUR_TOKEN_HERE
  ```

Good luck with your PyPI publication! 🚀
