API Reference
=============

This section provides reference documentation for the main modules, utility classes, configuration, and logging used in MAAS CPU Analyzer.

Core Modules
------------

MAAS CPU Analyzer
-----------------

maas_cpu_analyzer.maas_cpu_analyzer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: maas_cpu_analyzer.maas_cpu_analyzer
   :members:
   :undoc-members:
   :show-inheritance:

MAAS Client
-----------

maas_cpu_analyzer.maas_client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: maas_cpu_analyzer.maas_client
   :members:
   :undoc-members:
   :show-inheritance:

OpenStack Client
----------------

maas_cpu_analyzer.openstack_client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: maas_cpu_analyzer.openstack_client
   :members:
   :undoc-members:
   :show-inheritance:

Trait Manager
-------------

maas_cpu_analyzer.trait_manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: maas_cpu_analyzer.trait_manager
   :members:
   :undoc-members:
   :show-inheritance:

Utilities
---------

maas_cpu_analyzer.utils
~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: maas_cpu_analyzer.utils
   :members:
   :undoc-members:
   :show-inheritance:

Utility Classes
---------------

CPUUtils
~~~~~~~~

.. autoclass:: maas_cpu_analyzer.utils.CPUUtils
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

MachineFilterUtils
~~~~~~~~~~~~~~~~~~

.. autoclass:: maas_cpu_analyzer.utils.MachineFilterUtils
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

MessageUtils
~~~~~~~~~~~~

.. autoclass:: maas_cpu_analyzer.utils.MessageUtils
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

TableUtils
~~~~~~~~~~

.. autoclass:: maas_cpu_analyzer.utils.TableUtils
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

ValidationUtils
~~~~~~~~~~~~~~~

.. autoclass:: maas_cpu_analyzer.utils.ValidationUtils
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Error Handling
--------------

MAAS CPU Analyzer uses standard Python exceptions and custom error handling within its modules. See each module's documentation for details on specific error handling strategies.

Configuration
-------------

Configuration via Environment Variables and config.ini
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

MAAS CPU Analyzer can be configured using environment variables or a `config.ini` file. Environment variables always take precedence over values in `config.ini`.

**MAAS Configuration**

- ``MAAS_URL``: The MAAS API endpoint URL (including the full API path).
- ``MAAS_API_KEY``: The MAAS API key for authentication.

**OpenStack Configuration**

- ``OS_AUTH_URL``: The OpenStack authentication URL (Keystone endpoint).
- ``OS_USERNAME``: The OpenStack username.
- ``OS_PASSWORD``: The OpenStack password.
- ``OS_PROJECT_NAME``: The OpenStack project (tenant) name.
- ``OS_USER_DOMAIN_NAME`` (optional): The user domain name (default: "Default").
- ``OS_PROJECT_DOMAIN_NAME`` (optional): The project domain name (default: "Default").

For more details and configuration examples, refer to the "Configuration" section of the documentation.

Logging
-------

MAAS CPU Analyzer uses Python's standard logging module. Log messages are sent to stderr by default.

**Log Levels**

- ``INFO``: General information about the analysis process.
- ``WARNING``: Non-fatal issues that do not prevent operation.
- ``ERROR``: Fatal errors that prevent successful completion.
- ``DEBUG``: Detailed debugging information (enabled with verbose mode).

**Log Format**

Log messages use the following format:

.. code-block:: text

   [LEVEL] message

**Example:**

.. code-block:: text

   [INFO] Starting CPU analysis...
   [INFO] Found 5 machines to analyze
   [WARNING] Machine 'node-01' has no CPU information
   [ERROR] Failed to connect to OpenStack Placement service
