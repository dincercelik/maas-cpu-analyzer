"""MAAS CPU Analyzer - A tool to analyze CPU models in MAAS machines.

This tool analyzes CPU models in MAAS machines and optionally creates
OpenStack traits for resource scheduling.
"""

__version__ = "1.0.0"
__author__ = "Dincer Celik"
__email__ = "hello@dincercelik.com"

from .maas_cpu_analyzer import MAASCPUAnalyzer, main

__all__ = ["main", "MAASCPUAnalyzer"]
