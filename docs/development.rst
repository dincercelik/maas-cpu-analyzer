Development
============

This section provides information for developers who want to contribute to the MAAS CPU Analyzer project.

Getting Started
---------------

Prerequisites
~~~~~~~~~~~~~

* Python 3.9 or higher
* Git
* Virtual environment (venv, virtualenv, or conda)

Development Setup
~~~~~~~~~~~~~~~~~

1. Clone the repository:

   .. code-block:: bash

      git clone https://github.com/your-org/maas-cpu-analyzer.git
      cd maas-cpu-analyzer

2. Create a virtual environment:

   .. code-block:: bash

      python -m venv venv
      source venv/bin/activate  # On Windows: venv\Scripts\activate

3. Install development dependencies:

   .. code-block:: bash

      pip install -e ".[dev]"

4. Install pre-commit hooks:

   .. code-block:: bash

      pre-commit install

Project Structure
-----------------

.. code-block:: text

   maas-cpu-analyzer/
   ├── maas_cpu_analyzer/          # Main package
   │   ├── __init__.py
   │   ├── maas_cpu_analyzer.py    # Main CLI module
   │   ├── maas_client.py          # MAAS API client
   │   ├── openstack_client.py     # OpenStack client
   │   ├── trait_manager.py        # Trait management
   │   └── utils.py                # Utility functions
   ├── tests/                      # Test suite
   │   ├── unit/                   # Unit tests
   │   ├── integration/            # Integration tests
   │   └── performance/            # Performance tests
   ├── docs/                       # Documentation
   ├── requirements.txt            # Runtime dependencies
   ├── requirements-test.txt       # Development dependencies
   ├── pyproject.toml             # Project configuration
   ├── tox.ini                    # Tox configuration
   ├── .pre-commit-config.yaml    # Pre-commit hooks
   ├── .flake8                    # Flake8 configuration
   ├── .pylintrc                  # Pylint configuration
   └── Makefile                   # Development commands

Development Commands
--------------------

The project includes a Makefile with common development commands:

.. code-block:: bash

   make help                    # Show all available commands
   make install-dev            # Install in development mode
   make test                   # Run all tests
   make test-unit              # Run unit tests only
   make test-integration       # Run integration tests only
   make lint                   # Run linting checks
   make format                 # Format code with black and isort
   make security               # Run security checks
   make docs                   # Build documentation
   make clean                  # Clean build artifacts
   make docker-build           # Build Docker image
   make docker-compose-up      # Run with Docker Compose
   make docker-compose-dev     # Run development container

Testing
-------

Running Tests
~~~~~~~~~~~~~

Run all tests:

.. code-block:: bash

   make test
   # or
   pytest

Run specific test categories:

.. code-block:: bash

   make test-unit              # Unit tests
   make test-integration       # Integration tests
   make test-performance       # Performance tests

Run tests with coverage:

.. code-block:: bash

   make test-coverage

Using Tox
~~~~~~~~~

The project uses Tox for testing across multiple Python versions:

.. code-block:: bash

   tox                         # Run all test environments
   tox -e py39                 # Test on Python 3.9
   tox -e py310                # Test on Python 3.10
   tox -e py311                # Test on Python 3.11
   tox -e py312                # Test on Python 3.12
   tox -e lint                 # Run linting
   tox -e security             # Run security checks

Code Quality
------------

Linting
~~~~~~~

Run linting checks:

.. code-block:: bash

   make lint
   # or
   flake8 maas_cpu_analyzer/ tests/
   pylint maas_cpu_analyzer/

Formatting
~~~~~~~~~~

Format code automatically:

.. code-block:: bash

   make format
   # or
   black maas_cpu_analyzer/ tests/
   isort maas_cpu_analyzer/ tests/

Check formatting without making changes:

.. code-block:: bash

   make format-check

Security Checks
~~~~~~~~~~~~~~~

Run security scans:

.. code-block:: bash

   make security
   # or
   bandit -r maas_cpu_analyzer/ -ll
   pip-audit -r requirements.txt -r requirements-test.txt

Pre-commit Hooks
~~~~~~~~~~~~~~~~

The project uses pre-commit hooks to ensure code quality:

.. code-block:: bash

   pre-commit run --all-files  # Run all hooks
   pre-commit install          # Install hooks

Hooks include:
* Code formatting (black, isort)
* Linting (flake8, pylint)
* Security checks (bandit)
* Type checking (mypy)
* Testing (pytest)

Documentation
-------------

Building Documentation
~~~~~~~~~~~~~~~~~~~~~~

Build the documentation:

.. code-block:: bash

   make docs
   # or
   sphinx-build -W -b html docs/ docs/_build/html

The documentation will be available in ``docs/_build/html/index.html``.

Documentation Structure
~~~~~~~~~~~~~~~~~~~~~~~

* ``docs/index.rst`` - Main documentation page
* ``docs/installation.rst`` - Installation instructions
* ``docs/usage.rst`` - Usage guide
* ``docs/api.rst`` - API reference
* ``docs/configuration.rst`` - Configuration options
* ``docs/development.rst`` - Development guide
* ``docs/changelog.rst`` - Change log

Docker Development
------------------

The project includes Docker support for containerized development and deployment.

Docker Setup
~~~~~~~~~~~~

Build the Docker image:

.. code-block:: bash

   make docker-build

Run with Docker Compose (if available):

.. code-block:: bash

   # Copy and configure environment file
   cp docker.env.example .env
   # Edit .env with your actual configuration values

   # Run the container
   make docker-compose-up

   # Note: Docker Compose may not be available on all systems

Development Container
~~~~~~~~~~~~~~~~~~~~~

For development with live code reloading:

.. code-block:: bash

   make docker-compose-dev

This mounts the source code into the container, allowing you to make changes
and see them reflected immediately.

Docker Commands
~~~~~~~~~~~~~~~

Available Docker-related make targets:

.. code-block:: bash

   make docker-build           # Build Docker image
   make docker-run             # Run container (shows help)
   make docker-compose-up      # Run with Docker Compose
   make docker-compose-dev     # Run development container
   make docker-clean           # Clean Docker images and containers
   make clean-all              # Clean all artifacts including Docker

Contributing
------------

Pull Request Process
~~~~~~~~~~~~~~~~~~~~

1. Fork the repository
2. Create a feature branch: ``git checkout -b feature/your-feature``
3. Make your changes
4. Run tests: ``make test``
5. Run linting: ``make lint``
6. Run security checks: ``make security``
7. Commit your changes: ``git commit -m "Add your feature"``
8. Push to your fork: ``git push origin feature/your-feature``
9. Create a Pull Request

Code Style
~~~~~~~~~~

The project follows these style guidelines:

* **PEP 8**: Python code style guide
* **Black**: Code formatting
* **isort**: Import sorting
* **Google Style**: Docstring format
* **Type Hints**: Use type annotations where possible

Example code style:

.. code-block:: python

   def analyze_cpu_info(machine_data: Dict[str, Any]) -> Optional[CPUInfo]:
       """Analyze CPU information from machine data.

       Args:
           machine_data: Dictionary containing machine information from MAAS.

       Returns:
           CPUInfo object if CPU information is found, None otherwise.

       Raises:
           ValueError: If machine_data is invalid.
       """
       if not machine_data:
           raise ValueError("Machine data cannot be empty")

       # Implementation here
       return cpu_info

Commit Messages
~~~~~~~~~~~~~~~

Follow conventional commit format:

.. code-block:: text

   type(scope): description

   [optional body]

   [optional footer]

Examples:

.. code-block:: text

   feat(maas): add support for filtering by tags
   fix(openstack): handle authentication errors gracefully
   docs(api): update API documentation
   test(integration): add end-to-end tests

Release Process
---------------

Version Numbering
~~~~~~~~~~~~~~~~~

The project uses semantic versioning (MAJOR.MINOR.PATCH):

* **MAJOR**: Breaking changes
* **MINOR**: New features (backward compatible)
* **PATCH**: Bug fixes (backward compatible)

Release Steps
~~~~~~~~~~~~~

1. Update version in ``pyproject.toml``
2. Update ``CHANGELOG.md``
3. Create release tag: ``git tag v1.0.0``
4. Push tag: ``git push origin v1.0.0``
5. Build package: ``python -m build``
6. Upload to PyPI: ``twine upload dist/*``

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

Import Errors
^^^^^^^^^^^^^

If you encounter import errors:

.. code-block:: bash

   pip install -e .

Missing Dependencies
^^^^^^^^^^^^^^^^^^^^

Install missing dependencies:

.. code-block:: bash

   pip install -r requirements-test.txt

Test Failures
^^^^^^^^^^^^^

Run tests with verbose output:

.. code-block:: bash

   pytest -v

Check test coverage:

.. code-block:: bash

   pytest --cov=maas_cpu_analyzer

Documentation Build Errors
^^^^^^^^^^^^^^^^^^^^^^^^^^

Clean and rebuild documentation:

.. code-block:: bash

   make clean
   make docs
