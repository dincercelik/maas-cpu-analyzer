Configuration
==============

The MAAS CPU Analyzer can be configured through environment variables, command-line arguments, and configuration files.

Environment Variables
---------------------

MAAS Configuration
~~~~~~~~~~~~~~~~~~

These variables configure the connection to your MAAS server:

.. envvar:: MAAS_URL

   **Required**. The full URL to your MAAS API endpoint.

   Example:

   .. code-block:: bash

      export MAAS_URL="http://maas.example.com:5240/MAAS"

.. envvar:: MAAS_API_KEY

   **Required**. Your MAAS API key for authentication.

   You can find your API key in the MAAS web interface under:
   ``Account → API keys``

   Example:

   .. code-block:: bash

      export MAAS_API_KEY="your-api-key-here"

OpenStack Configuration
~~~~~~~~~~~~~~~~~~~~~~~

These variables configure the connection to your OpenStack environment:

.. envvar:: OS_AUTH_URL

   **Required**. The Keystone authentication URL for your OpenStack deployment.

   Example:

   .. code-block:: bash

      export OS_AUTH_URL="http://openstack.example.com:5000/v3"

.. envvar:: OS_USERNAME

   **Required**. Your OpenStack username.

   Example:

   .. code-block:: bash

      export OS_USERNAME="admin"

.. envvar:: OS_PASSWORD

   **Required**. Your OpenStack password.

   Example:

   .. code-block:: bash

      export OS_PASSWORD="your-password"

.. envvar:: OS_PROJECT_NAME

   **Required**. The OpenStack project (tenant) name.

   Example:

   .. code-block:: bash

      export OS_PROJECT_NAME="admin"

.. envvar:: OS_USER_DOMAIN_NAME

   **Optional**. The user domain name. Defaults to "Default".

   Example:

   .. code-block:: bash

      export OS_USER_DOMAIN_NAME="Default"

.. envvar:: OS_PROJECT_DOMAIN_NAME

   **Optional**. The project domain name. Defaults to "Default".

   Example:

   .. code-block:: bash

      export OS_PROJECT_DOMAIN_NAME="Default"

Network Configuration
~~~~~~~~~~~~~~~~~~~~~


Command-Line Arguments
----------------------

Filtering Options
~~~~~~~~~~~~~~~~~

.. option:: --zone ZONE

   Filter machines by zone name.

   Example:

   .. code-block:: bash

      maas-cpu-analyzer --zone compute

.. option:: --deployed-only

   Analyze only deployed machines.

   Example:

   .. code-block:: bash

      maas-cpu-analyzer --deployed-only

.. option:: --tags TAGS

   Filter machines by tags (comma-separated).

   Example:

   .. code-block:: bash

      maas-cpu-analyzer --tags production,compute

Output Options
~~~~~~~~~~~~~~

.. option:: --verbose

   Enable verbose output with detailed logging.

   Example:

   .. code-block:: bash

      maas-cpu-analyzer --verbose

.. option:: --version

   Show version information and exit.

   Example:

   .. code-block:: bash

      maas-cpu-analyzer --version

.. option:: --help

   Show help message and exit.

   Example:

   .. code-block:: bash

      maas-cpu-analyzer --help

Configuration Files
-------------------

The MAAS CPU Analyzer doesn't currently support configuration files, but all configuration can be done through environment variables and command-line arguments.

Example Configurations
----------------------

Development Environment
~~~~~~~~~~~~~~~~~~~~~~~

For development with shorter timeouts:

.. code-block:: bash

   export MAAS_URL="http://dev-maas:5240/MAAS"
   export MAAS_API_KEY="dev-api-key"
   export OS_AUTH_URL="http://dev-openstack:5000/v3"
   export OS_USERNAME="admin"
   export OS_PASSWORD="dev-password"
   export OS_PROJECT_NAME="admin"

Production Environment
~~~~~~~~~~~~~~~~~~~~~~

For production with longer timeouts and more retries:

.. code-block:: bash

   export MAAS_URL="https://prod-maas.example.com:5240/MAAS"
   export MAAS_API_KEY="prod-api-key"
   export OS_AUTH_URL="https://prod-openstack.example.com:5000/v3"
   export OS_USERNAME="maas-service"
   export OS_PASSWORD="secure-password"
   export OS_PROJECT_NAME="infrastructure"
   export OS_USER_DOMAIN_NAME="service"
   export OS_PROJECT_DOMAIN_NAME="default"

Docker Environment
~~~~~~~~~~~~~~~~~~

For Docker containers, set environment variables in the container:

.. code-block:: bash

   docker run -e MAAS_URL="http://maas:5240/MAAS" \
              -e MAAS_API_KEY="api-key" \
              -e OS_AUTH_URL="http://openstack:5000/v3" \
              -e OS_USERNAME="admin" \
              -e OS_PASSWORD="password" \
              -e OS_PROJECT_NAME="admin" \
              maas-cpu-analyzer

Security Considerations
-----------------------

API Keys and Passwords
~~~~~~~~~~~~~~~~~~~~~~

* Store API keys and passwords securely
* Use environment variables instead of hardcoding credentials
* Consider using a secrets management system for production
* Rotate credentials regularly

Network Security
~~~~~~~~~~~~~~~~

* Use HTTPS for production deployments
* Ensure proper firewall rules
* Consider VPN access for secure environments
* Monitor network traffic for anomalies

Access Control
~~~~~~~~~~~~~~

* Use dedicated service accounts with minimal required permissions
* Regularly audit access permissions
* Monitor API usage and access patterns
* Implement proper logging and alerting
