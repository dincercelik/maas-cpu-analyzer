"""Performance tests for MAAS CPU Analyzer."""

import pytest

from maas_cpu_analyzer import MAASCPUAnalyzer


class TestPerformance:
    """Performance test cases."""

    def test_analyzer_initialization_performance(self, benchmark):
        """Test that analyzer initialization is fast."""

        def init_analyzer():
            return MAASCPUAnalyzer(verbose=False)

        result = benchmark(init_analyzer)
        assert result is not None

    def test_cpu_model_parsing_performance(self, benchmark):
        """Test CPU model parsing performance."""
        analyzer = MAASCPUAnalyzer(verbose=False)

        # Test data with various CPU model strings
        cpu_models = [
            "Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz",
            "AMD EPYC 7551P 32-Core Processor",
            "Intel(R) Core(TM) i7-8700K CPU @ 3.70GHz",
            "AMD Ryzen 7 3700X 8-Core Processor",
            "Intel(R) Xeon(R) Gold 6248R CPU @ 3.00GHz",
        ]

        def parse_cpu_models():
            results = []
            for model in cpu_models:
                result = analyzer.get_cpu_vendor(model)
                results.append(result)
            return results

        result = benchmark(parse_cpu_models)
        assert len(result) == len(cpu_models)

    def test_trait_name_generation_performance(self, benchmark):
        """Test trait name generation performance."""
        analyzer = MAASCPUAnalyzer(verbose=False)

        cpu_models = [
            "Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz",
            "AMD EPYC 7551P 32-Core Processor",
            "Intel(R) Core(TM) i7-8700K CPU @ 3.70GHz",
        ]

        def generate_trait_names():
            results = []
            for model in cpu_models:
                trait_name = analyzer.generate_trait_name(model)
                results.append(trait_name)
            return results

        result = benchmark(generate_trait_names)
        assert len(result) == len(cpu_models)

    def test_memory_usage(self):
        """Test memory usage during normal operations."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Create multiple analyzer instances
        analyzers = []
        for _ in range(100):
            analyzer = MAASCPUAnalyzer(verbose=False)
            analyzers.append(analyzer)

        peak_memory = process.memory_info().rss
        memory_increase = peak_memory - initial_memory

        # Memory increase should be reasonable (less than 50MB)
        assert (
            memory_increase < 50 * 1024 * 1024
        ), f"Memory usage too high: {memory_increase / 1024 / 1024:.2f}MB"

        # Clean up
        del analyzers

    @pytest.mark.timeout(5)
    def test_timeout_protection(self):
        """Test that operations complete within reasonable time."""
        analyzer = MAASCPUAnalyzer(verbose=False)

        # This should complete quickly
        result = analyzer.get_cpu_vendor("Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz")
        assert result is not None
