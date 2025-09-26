MAAS CPU Analyzer Documentation
===============================

The MAAS CPU Analyzer is a tool for analyzing CPU configurations in MAAS (Metal as a Service) environments and managing CPU traits in OpenStack Placement service.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   usage
   api
   configuration
   development
   changelog

Features
--------

* **CPU Analysis**: Extract and analyze CPU information from MAAS machines
* **Trait Management**: Automatically create and manage CPU traits in OpenStack Placement
* **OpenStack Integration**: Seamless integration with OpenStack Placement service
* **Flexible Filtering**: Filter machines by zone, deployment status, and tags
* **Comprehensive Logging**: Detailed logging and verbose output options
* **Security Scanning**: Built-in security checks with bandit and pip-audit

Quick Start
-----------

Install the package:

.. code-block:: bash

   pip install maas-cpu-analyzer

Basic usage:

.. code-block:: bash

   # Analyze CPUs and create traits
   maas-cpu-analyzer --verbose

   # Filter by zone
   maas-cpu-analyzer --zone zone1

   # Deployed machines only
   maas-cpu-analyzer --deployed-only

   # With specific tags
   maas-cpu-analyzer --tags production,compute

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
