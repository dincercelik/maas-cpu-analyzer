Installation
============

Prerequisites
-------------

* Python 3.9 or higher
* Access to a MAAS server
* Access to an OpenStack environment with Placement service
* Network connectivity to both MAAS and OpenStack APIs

Install from PyPI
-----------------

The easiest way to install MAAS CPU Analyzer is using pip:

.. code-block:: bash

   pip install maas-cpu-analyzer

Install from Source
-------------------

Clone the repository and install in development mode:

.. code-block:: bash

   git clone https://github.com/your-org/maas-cpu-analyzer.git
   cd maas-cpu-analyzer
   pip install -e .

Install Development Dependencies
--------------------------------

For development and testing:

.. code-block:: bash

   pip install -e ".[dev]"

This will install additional dependencies for:

* Testing (pytest, pytest-mock, etc.)
* Code quality (flake8, black, isort, pylint)
* Security scanning (bandit, pip-audit)
* Documentation (sphinx, sphinx-rtd-theme)
* Performance testing (pytest-benchmark)

Environment Setup
-----------------

Set up the required environment variables:

.. code-block:: bash

   # MAAS Configuration
   export MAAS_URL="http://your-maas-server:5240/MAAS"
   export MAAS_API_KEY="your-api-key"

   # OpenStack Configuration
   export OS_AUTH_URL="http://your-openstack:5000/v3"
   export OS_USERNAME="your-username"
   export OS_PASSWORD="your-password"
   export OS_PROJECT_NAME="your-project"
   export OS_USER_DOMAIN_NAME="Default"
   export OS_PROJECT_DOMAIN_NAME="Default"

Verification
------------

Verify the installation:

.. code-block:: bash

   maas-cpu-analyzer --version
   maas-cpu-analyzer --help

Docker Installation
-------------------

You can run MAAS CPU Analyzer in a Docker container using the provided Dockerfile.

Build the Docker image:

.. code-block:: bash

   docker build -t maas-cpu-analyzer .

Run the container with environment variables:

.. code-block:: bash

   docker run --rm \
     -e MAAS_URL="http://your-maas:5240/MAAS" \
     -e MAAS_API_KEY="your-api-key" \
     -e OS_AUTH_URL="http://your-openstack:5000/v3" \
     -e OS_USERNAME="your-username" \
     -e OS_PASSWORD="your-password" \
     -e OS_PROJECT_NAME="your-project" \
     maas-cpu-analyzer --verbose

Using Docker Compose
~~~~~~~~~~~~~~~~~~~~

For easier management, use Docker Compose (if available):

1. Create a `.env` file with your configuration:

   .. code-block:: bash

      # Copy the example file
      cp docker.env.example .env

      # Edit with your actual values
      # MAAS_URL=http://your-maas:5240/MAAS
      # MAAS_API_KEY=your-api-key
      # OS_AUTH_URL=http://your-openstack:5000/v3
      # OS_USERNAME=your-username
      # OS_PASSWORD=your-password
      # OS_PROJECT_NAME=your-project

2. Run with Docker Compose:

   .. code-block:: bash

      docker-compose up maas-cpu-analyzer
      # or with newer Docker versions:
      docker compose up maas-cpu-analyzer

   **Note**: Docker Compose may not be available on all Docker installations.
   If you encounter issues, use the direct Docker commands above.

Development with Docker
~~~~~~~~~~~~~~~~~~~~~~~

For development with live code reloading:

.. code-block:: bash

   docker-compose up maas-cpu-analyzer-dev
