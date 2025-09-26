API Reference
==============

This section provides detailed API documentation for the MAAS CPU Analyzer.

Core Modules
------------

MAAS CPU Analyzer
~~~~~~~~~~~~~~~~~~

.. automodule:: maas_cpu_analyzer.maas_cpu_analyzer
   :members:
   :undoc-members:
   :show-inheritance:

MAAS Client
~~~~~~~~~~~

.. automodule:: maas_cpu_analyzer.maas_client
   :members:
   :undoc-members:
   :show-inheritance:

OpenStack Client
~~~~~~~~~~~~~~~~

.. automodule:: maas_cpu_analyzer.openstack_client
   :members:
   :undoc-members:
   :show-inheritance:

Trait Manager
~~~~~~~~~~~~~

.. automodule:: maas_cpu_analyzer.trait_manager
   :members:
   :undoc-members:
   :show-inheritance:

Utilities
~~~~~~~~~

.. automodule:: maas_cpu_analyzer.utils
   :members:
   :undoc-members:
   :show-inheritance:

Utility Classes
---------------

CPU Utils
~~~~~~~~~

.. autoclass:: maas_cpu_analyzer.utils.CPUUtils
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Machine Filter Utils
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: maas_cpu_analyzer.utils.MachineFilterUtils
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Message Utils
~~~~~~~~~~~~~

.. autoclass:: maas_cpu_analyzer.utils.MessageUtils
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Table Utils
~~~~~~~~~~~

.. autoclass:: maas_cpu_analyzer.utils.TableUtils
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Validation Utils
~~~~~~~~~~~~~~~~

.. autoclass:: maas_cpu_analyzer.utils.ValidationUtils
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Error Handling
--------------

The MAAS CPU Analyzer uses standard Python exceptions and custom error handling within the modules. See the individual module documentation for specific error handling patterns.

Configuration
-------------

Environment Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~

The following environment variables are used for configuration:

MAAS Configuration
^^^^^^^^^^^^^^^^^^

.. data:: MAAS_URL
   :annotation: str

   The MAAS API endpoint URL. Should include the full path to the API.

.. data:: MAAS_API_KEY
   :annotation: str

   The MAAS API key for authentication.

OpenStack Configuration
^^^^^^^^^^^^^^^^^^^^^^^

.. data:: OS_AUTH_URL
   :annotation: str

   The OpenStack authentication URL (Keystone endpoint).

.. data:: OS_USERNAME
   :annotation: str

   The OpenStack username for authentication.

.. data:: OS_PASSWORD
   :annotation: str

   The OpenStack password for authentication.

.. data:: OS_PROJECT_NAME
   :annotation: str

   The OpenStack project name.

.. data:: OS_USER_DOMAIN_NAME
   :annotation: str

   The user domain name for OpenStack authentication.

.. data:: OS_PROJECT_DOMAIN_NAME
   :annotation: str

   The project domain name for OpenStack authentication.


Logging
-------

The MAAS CPU Analyzer uses Python's standard logging module. Log messages are sent to stderr by default.

Log Levels
~~~~~~~~~~

* **INFO**: General information about the analysis process
* **WARNING**: Non-fatal issues that don't prevent operation
* **ERROR**: Fatal errors that prevent successful completion
* **DEBUG**: Detailed debugging information (requires verbose mode)

Log Format
~~~~~~~~~~

Log messages follow this format:

.. code-block:: text

   [LEVEL] message

Example:

.. code-block:: text

   [INFO] Starting CPU analysis...
   [INFO] Found 5 machines to analyze
   [WARNING] Machine 'node-01' has no CPU information
   [ERROR] Failed to connect to OpenStack Placement service
