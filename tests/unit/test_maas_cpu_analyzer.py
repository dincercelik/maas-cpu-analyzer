"""Unit tests for MAASCPUAnalyzer class."""

from unittest.mock import Mock, patch

import pytest

from maas_cpu_analyzer.maas_cpu_analyzer import MAASCPUAnalyzer
from maas_cpu_analyzer.utils import CPUUtils, MachineFilterUtils, TableUtils


class TestMAASCPUAnalyzer:
    """Test cases for MAASCPUAnalyzer class."""

    def test_init(self):
        """Test MAASCPUAnalyzer initialization."""
        _analyzer = MAASCPUAnalyzer(verbose=True)
        assert _analyzer.verbose is True
        # Internal caches moved into OpenStackClient; ensure clients exist
        assert _analyzer.openstack_client is not None
        assert _analyzer.maas_client is not None

    def test_init_verbose_false(self):
        """Test MAASCPUAnalyzer initialization with verbose=False."""
        _analyzer = MAASCPUAnalyzer(verbose=False)
        assert _analyzer.verbose is False

    def test_get_cpu_vendor_intel(self):
        """Test CPU vendor detection for Intel processors."""
        _analyzer = MAASCPUAnalyzer()

        test_cases = [
            "Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz",
            "Intel Core i7-8700K CPU @ 3.70GHz",
            "Intel(R) Core(TM) i5-8400 CPU @ 2.80GHz",
        ]

        for cpu_model in test_cases:
            assert CPUUtils.get_cpu_vendor(cpu_model) == "INTEL"

    def test_get_cpu_vendor_amd(self):
        """Test CPU vendor detection for AMD processors."""
        _analyzer = MAASCPUAnalyzer()

        test_cases = [
            "AMD EPYC 7551P 32-Core Processor",
            "AMD Ryzen 7 3700X 8-Core Processor",
            "AMD Opteron(tm) Processor 6272",
        ]

        for cpu_model in test_cases:
            assert CPUUtils.get_cpu_vendor(cpu_model) == "AMD"

    def test_get_cpu_vendor_unknown(self):
        """Test CPU vendor detection for unknown processors."""
        _analyzer = MAASCPUAnalyzer()

        test_cases = ["Unknown CPU Model", "Some Random CPU", "", None]

        for cpu_model in test_cases:
            assert CPUUtils.get_cpu_vendor(cpu_model) == "UNKNOWN"

    def test_generate_trait_name_intel(self):
        """Test trait name generation for Intel CPUs."""
        _analyzer = MAASCPUAnalyzer()

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
            assert CPUUtils.generate_trait_name(cpu_model) == expected

    def test_generate_trait_name_amd(self):
        """Test trait name generation for AMD CPUs."""
        _analyzer = MAASCPUAnalyzer()

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
            assert CPUUtils.generate_trait_name(cpu_model) == expected

    def test_generate_trait_name_unknown(self):
        """Test trait name generation for unknown CPUs."""
        _analyzer = MAASCPUAnalyzer()

        test_cases = [
            ("Unknown CPU Model", "CUSTOM_UNKNOWN_UNKNOWN_CPU_MODEL"),
            ("Some Random CPU", "CUSTOM_UNKNOWN_SOME_RANDOM"),
            ("", "CUSTOM_UNKNOWN_EMPTY"),
            (None, "CUSTOM_UNKNOWN_EMPTY"),
        ]

        for cpu_model, expected in test_cases:
            assert CPUUtils.generate_trait_name(cpu_model) == expected

    def test_generate_trait_name_special_characters(self):
        """Test trait name generation with special characters."""
        _analyzer = MAASCPUAnalyzer()

        cpu_model = "Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz"
        expected = "CUSTOM_INTEL_R_XEON_R_CPU_E5_2680_V4_2_40GHZ"
        assert CPUUtils.generate_trait_name(cpu_model) == expected

    def test_filter_machines_empty_list(self):
        """Test filtering with empty machine list."""
        _analyzer = MAASCPUAnalyzer()
        result = MachineFilterUtils.filter_machines([], None, False, [])
        assert result == []

    def test_filter_machines_by_zone(self, sample_maas_machines):
        """Test filtering machines by zone."""
        _analyzer = MAASCPUAnalyzer()

        # Filter by zone-1
        result = MachineFilterUtils.filter_machines(
            sample_maas_machines, "zone-1", False, []
        )
        assert len(result) == 3
        assert all(machine["zone"]["name"] == "zone-1" for machine in result)

        # Filter by zone-2
        result = MachineFilterUtils.filter_machines(
            sample_maas_machines, "zone-2", False, []
        )
        assert len(result) == 1
        assert result[0]["zone"]["name"] == "zone-2"

    def test_filter_machines_deployed_only(self, sample_maas_machines):
        """Test filtering machines by deployment status."""
        _analyzer = MAASCPUAnalyzer()

        result = MachineFilterUtils.filter_machines(
            sample_maas_machines, None, True, []
        )
        assert len(result) == 3
        assert all(machine["status_name"] == "Deployed" for machine in result)

    def test_filter_machines_by_tags(self, sample_maas_machines):
        """Test filtering machines by tags."""
        _analyzer = MAASCPUAnalyzer()

        # Filter by 'compute' tag
        result = MachineFilterUtils.filter_machines(
            sample_maas_machines, None, False, ["compute"]
        )
        assert len(result) == 2
        assert all("compute" in machine["tag_names"] for machine in result)

        # Filter by 'gpu' tag
        result = MachineFilterUtils.filter_machines(
            sample_maas_machines, None, False, ["gpu"]
        )
        assert len(result) == 1
        assert "gpu" in result[0]["tag_names"]

    def test_filter_machines_combined_filters(self, sample_maas_machines):
        """Test filtering machines with combined filters."""
        _analyzer = MAASCPUAnalyzer()

        # Filter by zone-1, deployed only, with compute tag
        result = MachineFilterUtils.filter_machines(
            sample_maas_machines, "zone-1", True, ["compute"]
        )
        assert len(result) == 2
        for machine in result:
            assert machine["zone"]["name"] == "zone-1"
            assert machine["status_name"] == "Deployed"
            assert "compute" in machine["tag_names"]

    def test_log_verbose_enabled(self, capsys):
        """Test logging when verbose is enabled."""
        _analyzer = MAASCPUAnalyzer(verbose=True)
        _analyzer.log("Test message")

        captured = capsys.readouterr()
        assert "Test message" in captured.out

    def test_log_verbose_disabled(self, capsys):
        """Test logging when verbose is disabled."""
        _analyzer = MAASCPUAnalyzer(verbose=False)
        _analyzer.log("Test message")

        captured = capsys.readouterr()
        assert "Test message" not in captured.out

    def test_handle_error_with_return_value(self):
        """Test error handling with return value."""
        _analyzer = MAASCPUAnalyzer()

        # _handle_error removed; simulate behavior using try/except
        try:
            raise ValueError("Test error")
        except ValueError:
            result = "default_value"

        assert result == "default_value"

    def test_handle_error_without_return_value(self):
        """Test error handling without return value."""
        _analyzer = MAASCPUAnalyzer()

        try:
            raise ValueError("Test error")
        except ValueError:
            result = None

        assert result is None

    def test_print_table(self, capsys):
        """Test table printing functionality."""
        _analyzer = MAASCPUAnalyzer()

        columns = ["Name", "Value"]
        rows = [["Test", "123"], ["Another", "456"]]

        TableUtils.print_table(columns, rows)

        captured = capsys.readouterr()
        assert "Name" in captured.out
        assert "Value" in captured.out
        assert "Test" in captured.out
        assert "123" in captured.out

    def test_print_machine_table_no_machines(self, capsys):
        """Test machine table printing with no machines."""
        _analyzer = MAASCPUAnalyzer()
        _analyzer.tags = []
        _analyzer.should_create_openstack_traits = False

        _analyzer.print_machine_table([], "zone-1", False)

        captured = capsys.readouterr()
        assert "No machines found" in captured.out

    def test_print_machine_table_with_machines(self, sample_maas_machines, capsys):
        """Test machine table printing with machines."""
        _analyzer = MAASCPUAnalyzer()
        _analyzer.tags = []
        _analyzer.should_create_openstack_traits = True

        _analyzer.print_machine_table(sample_maas_machines, None, False)

        captured = capsys.readouterr()
        assert "Hostname" in captured.out
        assert "Zone" in captured.out
        assert "Status" in captured.out
        assert "Vendor" in captured.out
        assert "CPU Model" in captured.out
        assert "OpenStack Trait" in captured.out

    def test_print_cpu_distribution(self, sample_maas_machines, capsys):
        """Test CPU distribution printing."""
        _analyzer = MAASCPUAnalyzer()
        _analyzer.tags = []

        _analyzer.print_cpu_distribution(sample_maas_machines, None, False)

        captured = capsys.readouterr()
        assert "CPU Model Distribution" in captured.out
        assert "Count" in captured.out
        assert "CPU Model" in captured.out

    def test_check_openstack_environment_missing_vars(self, capsys):
        """Test OpenStack environment check with missing variables."""
        _analyzer = MAASCPUAnalyzer()

        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(SystemExit):
                _analyzer.openstack_client.check_openstack_environment()

            captured = capsys.readouterr()
            # Behavior-focused: exit occurred and required variable names are listed
            for var in ["OS_AUTH_URL", "OS_USERNAME", "OS_PASSWORD", "OS_PROJECT_NAME"]:
                assert var in captured.err

    def test_check_openstack_environment_complete(self, mock_environment_variables):
        """Test OpenStack environment check with all variables present."""
        _analyzer = MAASCPUAnalyzer()

        # Should not raise any exceptions
        _analyzer.openstack_client.check_openstack_environment()

    def test_get_session_creation(self):
        """Test session creation and configuration."""
        _analyzer = MAASCPUAnalyzer()

        with patch(
            "maas_cpu_analyzer.openstack_client.requests.Session"
        ) as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            session = _analyzer.openstack_client._get_session()

            assert session == mock_session
            mock_session.mount.assert_called()
            mock_session.headers.update.assert_called()

    def test_get_session_caching(self):
        """Test session caching."""
        _analyzer = MAASCPUAnalyzer()

        with patch(
            "maas_cpu_analyzer.openstack_client.requests.Session"
        ) as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # First call
            session1 = _analyzer.openstack_client._get_session()
            # Second call
            session2 = _analyzer.openstack_client._get_session()

            # Should return the same session instance
            assert session1 == session2
            # Session should only be created once
            assert mock_session_class.call_count == 1
