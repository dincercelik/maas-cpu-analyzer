"""Unit tests for MAASCPUAnalyzer class."""

from unittest.mock import Mock, patch

import pytest

from maas_cpu_analyzer.maas_cpu_analyzer import MAASCPUAnalyzer


class TestMAASCPUAnalyzer:
    """Test cases for MAASCPUAnalyzer class."""

    def test_init(self):
        """Test MAASCPUAnalyzer initialization."""
        analyzer = MAASCPUAnalyzer(verbose=True)
        assert analyzer.verbose is True
        assert analyzer._auth_token is None
        assert analyzer._placement_endpoint is None
        assert analyzer._session is None
        assert analyzer._service_catalog is None
        assert analyzer._service_endpoints == {}

    def test_init_verbose_false(self):
        """Test MAASCPUAnalyzer initialization with verbose=False."""
        analyzer = MAASCPUAnalyzer(verbose=False)
        assert analyzer.verbose is False

    def test_get_cpu_vendor_intel(self):
        """Test CPU vendor detection for Intel processors."""
        analyzer = MAASCPUAnalyzer()

        test_cases = [
            "Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz",
            "Intel Core i7-8700K CPU @ 3.70GHz",
            "Intel(R) Core(TM) i5-8400 CPU @ 2.80GHz",
        ]

        for cpu_model in test_cases:
            assert analyzer.get_cpu_vendor(cpu_model) == "INTEL"

    def test_get_cpu_vendor_amd(self):
        """Test CPU vendor detection for AMD processors."""
        analyzer = MAASCPUAnalyzer()

        test_cases = [
            "AMD EPYC 7551P 32-Core Processor",
            "AMD Ryzen 7 3700X 8-Core Processor",
            "AMD Opteron(tm) Processor 6272",
        ]

        for cpu_model in test_cases:
            assert analyzer.get_cpu_vendor(cpu_model) == "AMD"

    def test_get_cpu_vendor_unknown(self):
        """Test CPU vendor detection for unknown processors."""
        analyzer = MAASCPUAnalyzer()

        test_cases = ["Unknown CPU Model", "Some Random CPU", "", None]

        for cpu_model in test_cases:
            assert analyzer.get_cpu_vendor(cpu_model) == "UNKNOWN"

    def test_generate_trait_name_intel(self):
        """Test trait name generation for Intel CPUs."""
        analyzer = MAASCPUAnalyzer()

        test_cases = [
            (
                "Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz",
                "CUSTOM_INTEL_R_XEON_R_CPU_E5_2680_V4_2_40GHZ",
            ),
            (
                "Intel Core i7-8700K CPU @ 3.70GHz",
                "CUSTOM_INTEL_CORE_I7_8700K_CPU_3_70GHZ",
            ),
            (
                "Intel(R) Core(TM) i5-8400 CPU @ 2.80GHz",
                "CUSTOM_INTEL_R_CORE_TM_I5_8400_CPU_2_80GHZ",
            ),
        ]

        for cpu_model, expected in test_cases:
            assert analyzer.generate_trait_name(cpu_model) == expected

    def test_generate_trait_name_amd(self):
        """Test trait name generation for AMD CPUs."""
        analyzer = MAASCPUAnalyzer()

        test_cases = [
            (
                "AMD EPYC 7551P 32-Core Processor",
                "CUSTOM_AMD_EPYC_7551P_32_CORE",
            ),
            (
                "AMD Ryzen 7 3700X 8-Core Processor",
                "CUSTOM_AMD_RYZEN_7_3700X_8_CORE",
            ),
        ]

        for cpu_model, expected in test_cases:
            assert analyzer.generate_trait_name(cpu_model) == expected

    def test_generate_trait_name_unknown(self):
        """Test trait name generation for unknown CPUs."""
        analyzer = MAASCPUAnalyzer()

        test_cases = [
            ("Unknown CPU Model", "CUSTOM_UNKNOWN_UNKNOWN_CPU_MODEL"),
            ("Some Random CPU", "CUSTOM_UNKNOWN_SOME_RANDOM"),
            ("", "CUSTOM_UNKNOWN_EMPTY"),
            (None, "CUSTOM_UNKNOWN_EMPTY"),
        ]

        for cpu_model, expected in test_cases:
            assert analyzer.generate_trait_name(cpu_model) == expected

    def test_generate_trait_name_special_characters(self):
        """Test trait name generation with special characters."""
        analyzer = MAASCPUAnalyzer()

        cpu_model = "Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz"
        expected = "CUSTOM_INTEL_R_XEON_R_CPU_E5_2680_V4_2_40GHZ"
        assert analyzer.generate_trait_name(cpu_model) == expected

    def test_filter_machines_empty_list(self):
        """Test filtering with empty machine list."""
        analyzer = MAASCPUAnalyzer()
        result = analyzer.filter_machines([], None, False, [])
        assert result == []

    def test_filter_machines_by_zone(self, sample_maas_machines):
        """Test filtering machines by zone."""
        analyzer = MAASCPUAnalyzer()

        # Filter by zone-1
        result = analyzer.filter_machines(sample_maas_machines, "zone-1", False, [])
        assert len(result) == 3
        assert all(machine["zone"]["name"] == "zone-1" for machine in result)

        # Filter by zone-2
        result = analyzer.filter_machines(sample_maas_machines, "zone-2", False, [])
        assert len(result) == 1
        assert result[0]["zone"]["name"] == "zone-2"

    def test_filter_machines_deployed_only(self, sample_maas_machines):
        """Test filtering machines by deployment status."""
        analyzer = MAASCPUAnalyzer()

        result = analyzer.filter_machines(sample_maas_machines, None, True, [])
        assert len(result) == 3
        assert all(machine["status_name"] == "Deployed" for machine in result)

    def test_filter_machines_by_tags(self, sample_maas_machines):
        """Test filtering machines by tags."""
        analyzer = MAASCPUAnalyzer()

        # Filter by 'compute' tag
        result = analyzer.filter_machines(
            sample_maas_machines, None, False, ["compute"]
        )
        assert len(result) == 2
        assert all("compute" in machine["tag_names"] for machine in result)

        # Filter by 'gpu' tag
        result = analyzer.filter_machines(sample_maas_machines, None, False, ["gpu"])
        assert len(result) == 1
        assert "gpu" in result[0]["tag_names"]

    def test_filter_machines_combined_filters(self, sample_maas_machines):
        """Test filtering machines with combined filters."""
        analyzer = MAASCPUAnalyzer()

        # Filter by zone-1, deployed only, with compute tag
        result = analyzer.filter_machines(
            sample_maas_machines, "zone-1", True, ["compute"]
        )
        assert len(result) == 2
        for machine in result:
            assert machine["zone"]["name"] == "zone-1"
            assert machine["status_name"] == "Deployed"
            assert "compute" in machine["tag_names"]

    def test_log_verbose_enabled(self, capsys):
        """Test logging when verbose is enabled."""
        analyzer = MAASCPUAnalyzer(verbose=True)
        analyzer.log("Test message")

        captured = capsys.readouterr()
        assert "Test message" in captured.err

    def test_log_verbose_disabled(self, capsys):
        """Test logging when verbose is disabled."""
        analyzer = MAASCPUAnalyzer(verbose=False)
        analyzer.log("Test message")

        captured = capsys.readouterr()
        assert "Test message" not in captured.err

    def test_handle_error_with_return_value(self):
        """Test error handling with return value."""
        analyzer = MAASCPUAnalyzer()

        error = ValueError("Test error")
        result = analyzer._handle_error(error, "test context", "default_value")

        assert result == "default_value"

    def test_handle_error_without_return_value(self):
        """Test error handling without return value."""
        analyzer = MAASCPUAnalyzer()

        error = ValueError("Test error")
        result = analyzer._handle_error(error, "test context")

        assert result is None

    def test_check_dependencies(self):
        """Test dependency checking."""
        analyzer = MAASCPUAnalyzer()
        # Should not raise any exceptions
        analyzer.check_dependencies()

    def test_clear_cache(self):
        """Test cache clearing."""
        analyzer = MAASCPUAnalyzer()

        # Set some cache values
        analyzer._auth_token = "test_token"
        analyzer._placement_endpoint = "test_endpoint"
        analyzer._service_catalog = {"test": "catalog"}
        analyzer._service_endpoints = {"test": "endpoint"}

        # Clear cache
        analyzer._clear_cache()

        assert analyzer._auth_token is None
        assert analyzer._placement_endpoint is None
        assert analyzer._service_catalog is None
        assert analyzer._service_endpoints == {}

    def test_print_table(self, capsys):
        """Test table printing functionality."""
        analyzer = MAASCPUAnalyzer()

        columns = ["Name", "Value"]
        rows = [["Test", "123"], ["Another", "456"]]

        analyzer.print_table(columns, rows)

        captured = capsys.readouterr()
        assert "Name" in captured.out
        assert "Value" in captured.out
        assert "Test" in captured.out
        assert "123" in captured.out

    def test_print_machine_table_no_machines(self, capsys):
        """Test machine table printing with no machines."""
        analyzer = MAASCPUAnalyzer()
        analyzer.tags = []
        analyzer.should_create_openstack_traits = False

        analyzer.print_machine_table([], "zone-1", False)

        captured = capsys.readouterr()
        assert "No machines found" in captured.out

    def test_print_machine_table_with_machines(self, sample_maas_machines, capsys):
        """Test machine table printing with machines."""
        analyzer = MAASCPUAnalyzer()
        analyzer.tags = []
        analyzer.should_create_openstack_traits = True

        analyzer.print_machine_table(sample_maas_machines, None, False)

        captured = capsys.readouterr()
        assert "Hostname" in captured.out
        assert "Zone" in captured.out
        assert "Status" in captured.out
        assert "Vendor" in captured.out
        assert "CPU Model" in captured.out
        assert "OpenStack Trait" in captured.out

    def test_print_cpu_distribution(self, sample_maas_machines, capsys):
        """Test CPU distribution printing."""
        analyzer = MAASCPUAnalyzer()
        analyzer.tags = []

        analyzer.print_cpu_distribution(sample_maas_machines, None, False)

        captured = capsys.readouterr()
        assert "CPU Model Distribution" in captured.out
        assert "Count" in captured.out
        assert "CPU Model" in captured.out

    def test_check_openstack_environment_missing_vars(self, capsys):
        """Test OpenStack environment check with missing variables."""
        analyzer = MAASCPUAnalyzer()

        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(SystemExit):
                analyzer.check_openstack_environment()

            captured = capsys.readouterr()
            assert "Missing required OpenStack environment variables" in captured.err

    def test_check_openstack_environment_complete(self, mock_environment_variables):
        """Test OpenStack environment check with all variables present."""
        analyzer = MAASCPUAnalyzer()

        # Should not raise any exceptions
        analyzer.check_openstack_environment()

    def test_get_session_creation(self):
        """Test session creation and configuration."""
        analyzer = MAASCPUAnalyzer()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            session = analyzer._get_session()

            assert session == mock_session
            mock_session.mount.assert_called()
            mock_session.headers.update.assert_called()

    def test_get_session_caching(self):
        """Test session caching."""
        analyzer = MAASCPUAnalyzer()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # First call
            session1 = analyzer._get_session()
            # Second call
            session2 = analyzer._get_session()

            # Should return the same session instance
            assert session1 == session2
            # Session should only be created once
            assert mock_session_class.call_count == 1
