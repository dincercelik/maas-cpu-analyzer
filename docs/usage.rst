Usage
=====

Command Line Interface
-----------------------

The MAAS CPU Analyzer provides a command-line interface for analyzing CPU configurations and managing traits.

Basic Usage
-----------

Analyze CPUs and create traits for all machines:

.. code-block:: bash

   maas-cpu-analyzer

Enable verbose output:

.. code-block:: bash

   maas-cpu-analyzer --verbose

Command Options
---------------

The MAAS CPU Analyzer supports the following command-line options:

.. option:: --zone ZONE

   Filter machines by zone name.

.. option:: --deployed-only

   Analyze only deployed machines.

.. option:: --tags TAGS

   Filter machines by tags (comma-separated).

.. option:: --verbose

   Enable verbose output with detailed logging.

.. option:: --version

   Show version information and exit.

.. option:: --help

   Show help message and exit.

Filtering Options
-----------------

Filter by Zone
~~~~~~~~~~~~~~

Analyze only machines in a specific zone:

.. code-block:: bash

   maas-cpu-analyzer --zone zone1

Filter by Deployment Status
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Analyze only deployed machines:

.. code-block:: bash

   maas-cpu-analyzer --deployed-only

Filter by Tags
~~~~~~~~~~~~~~

Analyze machines with specific tags:

.. code-block:: bash

   # Single tag
   maas-cpu-analyzer --tags production

   # Multiple tags (comma-separated)
   maas-cpu-analyzer --tags production,compute,gpu

Output Options
--------------

Verbose Logging
~~~~~~~~~~~~~~~

Enable detailed logging output:

.. code-block:: bash

   maas-cpu-analyzer --verbose

This will show:
* Detailed progress information
* HTTP requests and responses
* Trait creation and management details
* Error diagnostics

Configuration
--------------

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

The tool uses environment variables for configuration:

MAAS Configuration:

.. code-block:: bash

   MAAS_URL              # MAAS API endpoint URL
   MAAS_API_KEY          # MAAS API key

OpenStack Configuration:

.. code-block:: bash

   OS_AUTH_URL           # OpenStack authentication URL
   OS_USERNAME           # OpenStack username
   OS_PASSWORD           # OpenStack password
   OS_PROJECT_NAME       # OpenStack project name
   OS_USER_DOMAIN_NAME   # User domain name
   OS_PROJECT_DOMAIN_NAME # Project domain name

Examples
--------

Basic Analysis
~~~~~~~~~~~~~~

Analyze all machines and create CPU traits:

.. code-block:: bash

   maas-cpu-analyzer --verbose

Production Environment
~~~~~~~~~~~~~~~~~~~~~~

Analyze only production machines in the compute zone:

.. code-block:: bash

   maas-cpu-analyzer --zone compute --tags production --verbose

Testing Environment
~~~~~~~~~~~~~~~~~~~

Analyze only deployed machines in testing environment:

.. code-block:: bash

   maas-cpu-analyzer --deployed-only --tags testing --verbose

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

Authentication Failures
^^^^^^^^^^^^^^^^^^^^^^^

If you encounter authentication issues:

1. Verify your MAAS API key is correct
2. Check OpenStack credentials
3. Ensure network connectivity to both services

Network Timeouts
^^^^^^^^^^^^^^^^

Permission Errors
^^^^^^^^^^^^^^^^^

Ensure your OpenStack user has:
* Placement service access
* Resource provider modification permissions
* Trait creation permissions

Debug Mode
^^^^^^^^^^

Enable verbose logging for detailed diagnostics:

.. code-block:: bash

   maas-cpu-analyzer --verbose
