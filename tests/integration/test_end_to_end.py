"""End-to-end integration tests for MAAS CPU Analyzer."""

from unittest.mock import Mock, patch

import pytest

from maas_cpu_analyzer.maas_cpu_analyzer import MAASCPUAnalyzer


class TestEndToEnd:
    """End-to-end integration test cases."""

    def test_full_workflow_without_openstack(self, sample_maas_machines, capsys):
        """Test the complete workflow without OpenStack operations."""
        analyzer = MAASCPUAnalyzer(verbose=True)

        with patch.object(
            analyzer, "fetch_maas_data", return_value=sample_maas_machines
        ):
            analyzer.run(
                zone=None,
                deployed_only=False,
                tags=[],
                create_openstack_traits=False,
                assign_traits_to_hypervisors=False,
                clear_openstack_traits=False,
            )

            captured = capsys.readouterr()

            # Check that machine table was printed
            assert "Hostname" in captured.out
            assert "Zone" in captured.out
            assert "Status" in captured.out
            assert "Vendor" in captured.out
            assert "CPU Model" in captured.out

            # Check that CPU distribution was printed
            assert "CPU Model Distribution" in captured.out
            assert "Count" in captured.out

    def test_full_workflow_with_openstack_traits(
        self, sample_maas_machines, mock_environment_variables, capsys
    ):
        """Test the complete workflow with OpenStack trait creation."""
        analyzer = MAASCPUAnalyzer(verbose=True)

        with patch.object(
            analyzer, "fetch_maas_data", return_value=sample_maas_machines
        ):
            with patch.object(
                analyzer, "_check_openstack_connectivity", return_value=True
            ):
                with patch.object(
                    analyzer, "_create_trait", return_value=(True, "created")
                ):
                    analyzer.run(
                        zone=None,
                        deployed_only=False,
                        tags=[],
                        create_openstack_traits=True,
                        assign_traits_to_hypervisors=False,
                        clear_openstack_traits=False,
                    )

                    captured = capsys.readouterr()

                    # Check that trait creation was attempted
                    assert "Creating OpenStack Traits" in captured.out
                    assert "Summary" in captured.out

    def test_full_workflow_with_hypervisor_assignment(
        self, sample_maas_machines, mock_environment_variables, capsys
    ):
        """Test the complete workflow with hypervisor trait assignment."""
        analyzer = MAASCPUAnalyzer(verbose=True)

        with patch.object(
            analyzer, "fetch_maas_data", return_value=sample_maas_machines
        ):
            with patch.object(
                analyzer, "_check_openstack_connectivity", return_value=True
            ):
                with patch.object(
                    analyzer, "_create_trait", return_value=(True, "created")
                ):
                    with patch.object(analyzer, "_get_hypervisors", return_value=[]):
                        with patch.object(
                            analyzer, "_get_resource_providers", return_value=[]
                        ):
                            analyzer.run(
                                zone=None,
                                deployed_only=False,
                                tags=[],
                                create_openstack_traits=True,
                                assign_traits_to_hypervisors=True,
                                clear_openstack_traits=False,
                            )

                            captured = capsys.readouterr()

                            # Check that hypervisor assignment was attempted
                            assert "Assigning CPU Traits to Hypervisors" in captured.out

    def test_clear_openstack_traits_workflow(self, mock_environment_variables, capsys):
        """Test the clear OpenStack traits workflow."""
        analyzer = MAASCPUAnalyzer(verbose=True)

        with patch.object(analyzer, "_check_openstack_connectivity", return_value=True):
            with patch.object(analyzer, "_get_resource_providers", return_value=[]):
                with patch.object(
                    analyzer, "_make_placement_api_request"
                ) as mock_request:
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {"traits": []}
                    mock_request.return_value = mock_response

                    analyzer.run(
                        zone=None,
                        deployed_only=False,
                        tags=[],
                        create_openstack_traits=False,
                        assign_traits_to_hypervisors=False,
                        clear_openstack_traits=True,
                    )

                    captured = capsys.readouterr()

                    # Check that trait clearing was attempted
                    assert "Clearing OpenStack Traits" in captured.out

    def test_workflow_with_zone_filter(self, sample_maas_machines, capsys):
        """Test workflow with zone filtering."""
        analyzer = MAASCPUAnalyzer(verbose=True)

        with patch.object(
            analyzer, "fetch_maas_data", return_value=sample_maas_machines
        ):
            analyzer.run(
                zone="zone-1",
                deployed_only=False,
                tags=[],
                create_openstack_traits=False,
                assign_traits_to_hypervisors=False,
                clear_openstack_traits=False,
            )

            captured = capsys.readouterr()

            # Check that zone filtering was applied
            assert "zone-1" in captured.out

    def test_workflow_with_deployed_only_filter(self, sample_maas_machines, capsys):
        """Test workflow with deployed-only filtering."""
        analyzer = MAASCPUAnalyzer(verbose=True)

        with patch.object(
            analyzer, "fetch_maas_data", return_value=sample_maas_machines
        ):
            analyzer.run(
                zone=None,
                deployed_only=True,
                tags=[],
                create_openstack_traits=False,
                assign_traits_to_hypervisors=False,
                clear_openstack_traits=False,
            )

            captured = capsys.readouterr()

            # Check that deployed-only filtering was applied
            assert "deployed" in captured.out

    def test_workflow_with_tag_filter(self, sample_maas_machines, capsys):
        """Test workflow with tag filtering."""
        analyzer = MAASCPUAnalyzer(verbose=True)

        with patch.object(
            analyzer, "fetch_maas_data", return_value=sample_maas_machines
        ):
            analyzer.run(
                zone=None,
                deployed_only=False,
                tags=["compute"],
                create_openstack_traits=False,
                assign_traits_to_hypervisors=False,
                clear_openstack_traits=False,
            )

            captured = capsys.readouterr()

            # Check that tag filtering was applied
            assert "compute" in captured.out

    def test_workflow_with_combined_filters(self, sample_maas_machines, capsys):
        """Test workflow with combined filters."""
        analyzer = MAASCPUAnalyzer(verbose=True)

        with patch.object(
            analyzer, "fetch_maas_data", return_value=sample_maas_machines
        ):
            analyzer.run(
                zone="zone-1",
                deployed_only=True,
                tags=["compute"],
                create_openstack_traits=False,
                assign_traits_to_hypervisors=False,
                clear_openstack_traits=False,
            )

            captured = capsys.readouterr()

            # Check that all filters were applied
            assert "zone-1" in captured.out
            assert "deployed" in captured.out
            assert "compute" in captured.out

    def test_workflow_error_handling(self, capsys):
        """Test workflow error handling."""
        analyzer = MAASCPUAnalyzer(verbose=True)

        with patch.object(
            analyzer, "fetch_maas_data", side_effect=Exception("Test error")
        ):
            with pytest.raises(Exception, match="Test error"):
                analyzer.run(
                    zone=None,
                    deployed_only=False,
                    tags=[],
                    create_openstack_traits=False,
                    assign_traits_to_hypervisors=False,
                    clear_openstack_traits=False,
                )

    def test_workflow_verbose_logging(self, sample_maas_machines, capsys):
        """Test verbose logging throughout the workflow."""
        analyzer = MAASCPUAnalyzer(verbose=True)

        with patch.object(
            analyzer, "fetch_maas_data", return_value=sample_maas_machines
        ):
            analyzer.run(
                zone=None,
                deployed_only=False,
                tags=[],
                create_openstack_traits=False,
                assign_traits_to_hypervisors=False,
                clear_openstack_traits=False,
            )

            captured = capsys.readouterr()

            # Check that verbose logging was active
            assert "Script completed successfully" in captured.err

    def test_workflow_no_verbose_logging(self, sample_maas_machines, capsys):
        """Test workflow without verbose logging."""
        analyzer = MAASCPUAnalyzer(verbose=False)

        with patch.object(
            analyzer, "fetch_maas_data", return_value=sample_maas_machines
        ):
            analyzer.run(
                zone=None,
                deployed_only=False,
                tags=[],
                create_openstack_traits=False,
                assign_traits_to_hypervisors=False,
                clear_openstack_traits=False,
            )

            captured = capsys.readouterr()

            # Check that verbose logging was not active
            assert "Script completed successfully" not in captured.err

    # --- MISSING TESTS BELOW ---

    def test_workflow_handles_missing_maas_config(self, capsys):
        """Test workflow exits if MAAS config is missing."""
        analyzer = MAASCPUAnalyzer(verbose=True)
        # Simulate fetch_maas_data calling sys.exit due to missing config
        with patch.object(analyzer, "fetch_maas_data", side_effect=SystemExit(1)):
            with pytest.raises(SystemExit):
                analyzer.run(
                    zone=None,
                    deployed_only=False,
                    tags=[],
                    create_openstack_traits=False,
                    assign_traits_to_hypervisors=False,
                    clear_openstack_traits=False,
                )

    def test_workflow_handles_invalid_maas_api_key(self, sample_maas_machines, capsys):
        """Test workflow exits if MAAS API key is invalid format."""
        analyzer = MAASCPUAnalyzer(verbose=True)
        # Simulate fetch_maas_data calling sys.exit due to invalid API key
        with patch.object(analyzer, "fetch_maas_data", side_effect=SystemExit(1)):
            with pytest.raises(SystemExit):
                analyzer.run(
                    zone=None,
                    deployed_only=False,
                    tags=[],
                    create_openstack_traits=False,
                    assign_traits_to_hypervisors=False,
                    clear_openstack_traits=False,
                )

    def test_workflow_handles_openstack_missing_config(
        self, sample_maas_machines, capsys
    ):
        """Test workflow exits if OpenStack config is missing and OpenStack features are requested."""
        analyzer = MAASCPUAnalyzer(verbose=True)
        with patch.object(
            analyzer, "fetch_maas_data", return_value=sample_maas_machines
        ):
            # Simulate _check_openstack_connectivity calling sys.exit due to missing config
            with patch.object(
                analyzer, "_check_openstack_connectivity", side_effect=SystemExit(1)
            ):
                with pytest.raises(SystemExit):
                    analyzer.run(
                        zone=None,
                        deployed_only=False,
                        tags=[],
                        create_openstack_traits=True,
                        assign_traits_to_hypervisors=False,
                        clear_openstack_traits=False,
                    )

    def test_workflow_handles_openstack_trait_creation_failure(
        self, sample_maas_machines, mock_environment_variables, capsys
    ):
        """Test workflow handles OpenStack trait creation failure gracefully."""
        analyzer = MAASCPUAnalyzer(verbose=True)
        with patch.object(
            analyzer, "fetch_maas_data", return_value=sample_maas_machines
        ):
            with patch.object(
                analyzer, "_check_openstack_connectivity", return_value=True
            ):
                with patch.object(
                    analyzer, "_create_trait", return_value=(False, "error")
                ):
                    analyzer.run(
                        zone=None,
                        deployed_only=False,
                        tags=[],
                        create_openstack_traits=True,
                        assign_traits_to_hypervisors=False,
                        clear_openstack_traits=False,
                    )
                    captured = capsys.readouterr()
                    assert "error" in captured.out or "failed" in captured.out.lower()

    def test_workflow_handles_openstack_trait_assignment_failure(
        self, sample_maas_machines, mock_environment_variables, capsys
    ):
        """Test workflow handles OpenStack trait assignment failure gracefully."""
        analyzer = MAASCPUAnalyzer(verbose=True)
        with patch.object(
            analyzer, "fetch_maas_data", return_value=sample_maas_machines
        ):
            with patch.object(
                analyzer.openstack_client,
                "_get_openstack_token",
                return_value="fake-token",
            ):
                with patch.object(
                    analyzer.openstack_client,
                    "check_openstack_connectivity",
                    return_value=True,
                ):
                    with patch.object(
                        analyzer.openstack_client, "get_hypervisors", return_value=[]
                    ):
                        with patch.object(
                            analyzer.openstack_client,
                            "get_resource_providers",
                            return_value=[],
                        ):
                            with patch.object(
                                analyzer.openstack_client,
                                "create_trait",
                                side_effect=Exception("assignment error"),
                            ):
                                analyzer.run(
                                    zone=None,
                                    deployed_only=False,
                                    tags=[],
                                    create_openstack_traits=True,
                                    assign_traits_to_hypervisors=True,
                                    clear_openstack_traits=False,
                                )
                                captured = capsys.readouterr()
                                assert (
                                    "assignment error" in captured.out
                                    or "Error" in captured.out
                                )

    def test_workflow_handles_openstack_trait_clearing_failure(
        self, mock_environment_variables, capsys
    ):
        """Test workflow handles OpenStack trait clearing failure gracefully."""
        analyzer = MAASCPUAnalyzer(verbose=True)
        with patch.object(
            analyzer.openstack_client, "_get_openstack_token", return_value="fake-token"
        ):
            with patch.object(
                analyzer.openstack_client,
                "check_openstack_connectivity",
                return_value=True,
            ):
                with patch.object(
                    analyzer.openstack_client,
                    "get_resource_providers",
                    return_value=[{"uuid": "test-uuid", "name": "test-provider"}],
                ):
                    with patch.object(
                        analyzer.openstack_client,
                        "make_placement_api_request",
                        side_effect=Exception("clear error"),
                    ):
                        analyzer.run(
                            zone=None,
                            deployed_only=False,
                            tags=[],
                            create_openstack_traits=False,
                            assign_traits_to_hypervisors=False,
                            clear_openstack_traits=True,
                        )
                        captured = capsys.readouterr()
                        assert "clear error" in captured.err or "Error" in captured.err

    def test_workflow_handles_empty_maas_data(self, capsys):
        """Test workflow handles empty MAAS data gracefully."""
        analyzer = MAASCPUAnalyzer(verbose=True)
        with patch.object(analyzer, "fetch_maas_data", return_value=[]):
            analyzer.run(
                zone=None,
                deployed_only=False,
                tags=[],
                create_openstack_traits=False,
                assign_traits_to_hypervisors=False,
                clear_openstack_traits=False,
            )
            captured = capsys.readouterr()
            assert (
                "No machines found" in captured.out or "no data" in captured.out.lower()
            )

    def test_workflow_handles_invalid_filter_combination(
        self, sample_maas_machines, capsys
    ):
        """Test workflow handles invalid filter combination gracefully."""
        analyzer = MAASCPUAnalyzer(verbose=True)
        # Simulate a filter combination that results in no machines
        with patch.object(
            analyzer, "fetch_maas_data", return_value=sample_maas_machines
        ):
            analyzer.run(
                zone="nonexistent-zone",
                deployed_only=True,
                tags=["nonexistent-tag"],
                create_openstack_traits=False,
                assign_traits_to_hypervisors=False,
                clear_openstack_traits=False,
            )
            captured = capsys.readouterr()
            assert (
                "No machines found" in captured.out or "no data" in captured.out.lower()
            )
