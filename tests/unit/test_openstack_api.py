"""Unit tests for OpenStack API interactions."""

import json
from unittest.mock import MagicMock, Mock, patch

import pytest

from maas_cpu_analyzer.maas_cpu_analyzer import MAASCPUAnalyzer


class TestOpenStackAPI:
    """Test cases for OpenStack API interactions."""

    def test_get_openstack_token_success(self, mock_environment_variables):
        """Test successful OpenStack token retrieval."""
        analyzer = MAASCPUAnalyzer()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.headers = {"X-Subject-Token": "test-token-12345"}
            mock_session.post.return_value = mock_response

            token = analyzer._get_openstack_token()

            assert token == "test-token-12345"
            assert analyzer._auth_token == "test-token-12345"

    def test_get_openstack_token_cached(self, mock_environment_variables):
        """Test OpenStack token caching."""
        analyzer = MAASCPUAnalyzer()
        analyzer._auth_token = "cached-token"

        token = analyzer._get_openstack_token()

        assert token == "cached-token"

    def test_get_openstack_token_missing_env_vars(self):
        """Test OpenStack token retrieval with missing environment variables."""
        analyzer = MAASCPUAnalyzer()

        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(
                ValueError, match="Missing required OpenStack environment variables"
            ):
                analyzer._get_openstack_token()

    def test_get_openstack_token_auth_failure(self, mock_environment_variables):
        """Test OpenStack token retrieval with authentication failure."""
        analyzer = MAASCPUAnalyzer()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_session.post.return_value = mock_response

            token = analyzer._get_openstack_token()

            assert token is None

    def test_get_openstack_token_no_token_in_headers(self, mock_environment_variables):
        """Test OpenStack token retrieval when no token in response headers."""
        analyzer = MAASCPUAnalyzer()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.headers = {}  # No X-Subject-Token header
            mock_session.post.return_value = mock_response

            token = analyzer._get_openstack_token()

            assert token is None

    def test_get_service_catalog_success(
        self, mock_environment_variables, mock_service_catalog
    ):
        """Test successful service catalog retrieval."""
        analyzer = MAASCPUAnalyzer()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_service_catalog
            mock_session.get.return_value = mock_response

            # Mock the token retrieval
            with patch.object(
                analyzer, "_get_openstack_token", return_value="test-token"
            ):
                catalog = analyzer._get_service_catalog()

                assert catalog == mock_service_catalog
                assert analyzer._service_catalog == mock_service_catalog

    def test_get_service_catalog_cached(
        self, mock_environment_variables, mock_service_catalog
    ):
        """Test service catalog caching."""
        analyzer = MAASCPUAnalyzer()
        analyzer._service_catalog = mock_service_catalog

        catalog = analyzer._get_service_catalog()

        assert catalog == mock_service_catalog

    def test_get_service_catalog_no_auth_url(self):
        """Test service catalog retrieval with no auth URL."""
        analyzer = MAASCPUAnalyzer()

        with patch.dict("os.environ", {}, clear=True):
            catalog = analyzer._get_service_catalog()

            assert catalog is None

    def test_get_service_catalog_invalid_structure(self, mock_environment_variables):
        """Test service catalog retrieval with invalid catalog structure."""
        analyzer = MAASCPUAnalyzer()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "invalid": "structure"
            }  # No 'catalog' key
            mock_session.get.return_value = mock_response

            with patch.object(
                analyzer, "_get_openstack_token", return_value="test-token"
            ):
                catalog = analyzer._get_service_catalog()

                assert catalog is None

    def test_get_service_endpoint_success(
        self, mock_environment_variables, mock_service_catalog
    ):
        """Test successful service endpoint retrieval."""
        analyzer = MAASCPUAnalyzer()

        with patch.object(
            analyzer, "_get_service_catalog", return_value=mock_service_catalog
        ):
            endpoint = analyzer._get_service_endpoint("placement", "public")

            assert endpoint == "http://test-openstack:8778"

    def test_get_service_endpoint_cached(self, mock_environment_variables):
        """Test service endpoint caching."""
        analyzer = MAASCPUAnalyzer()
        analyzer._service_endpoints["placement:public"] = "cached-endpoint"

        endpoint = analyzer._get_service_endpoint("placement", "public")

        assert endpoint == "cached-endpoint"

    def test_get_service_endpoint_no_catalog(self, mock_environment_variables):
        """Test service endpoint retrieval with no service catalog."""
        analyzer = MAASCPUAnalyzer()

        with patch.object(analyzer, "_get_service_catalog", return_value=None):
            endpoint = analyzer._get_service_endpoint("placement", "public")

            assert endpoint is None

    def test_get_service_endpoint_service_not_found(
        self, mock_environment_variables, mock_service_catalog
    ):
        """Test service endpoint retrieval when service is not found."""
        analyzer = MAASCPUAnalyzer()

        with patch.object(
            analyzer, "_get_service_catalog", return_value=mock_service_catalog
        ):
            endpoint = analyzer._get_service_endpoint("nonexistent", "public")

            assert endpoint is None

    def test_get_placement_endpoint_success(self, mock_environment_variables):
        """Test successful placement endpoint retrieval."""
        analyzer = MAASCPUAnalyzer()

        with patch.object(
            analyzer, "_get_service_endpoint", return_value="http://test:8778"
        ):
            endpoint = analyzer._get_placement_endpoint()

            assert endpoint == "http://test:8778"
            assert analyzer._placement_endpoint == "http://test:8778"

    def test_get_placement_endpoint_cached(self, mock_environment_variables):
        """Test placement endpoint caching."""
        analyzer = MAASCPUAnalyzer()
        analyzer._placement_endpoint = "cached-endpoint"

        endpoint = analyzer._get_placement_endpoint()

        assert endpoint == "cached-endpoint"

    def test_get_placement_endpoint_not_found(self, mock_environment_variables):
        """Test placement endpoint retrieval when service is not found."""
        analyzer = MAASCPUAnalyzer()

        with patch.object(analyzer, "_get_service_endpoint", return_value=None):
            endpoint = analyzer._get_placement_endpoint()

            assert endpoint is None

    def test_get_resource_providers_success(
        self, mock_environment_variables, sample_resource_providers
    ):
        """Test successful resource providers retrieval."""
        analyzer = MAASCPUAnalyzer()

        with patch.object(analyzer, "_make_placement_api_request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "resource_providers": sample_resource_providers
            }
            mock_request.return_value = mock_response

            providers = analyzer._get_resource_providers()

            assert providers == sample_resource_providers
            mock_request.assert_called_once_with("GET", "/resource_providers")

    def test_get_resource_providers_failure(self, mock_environment_variables):
        """Test resource providers retrieval failure."""
        analyzer = MAASCPUAnalyzer()

        with patch.object(analyzer, "_make_placement_api_request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_request.return_value = mock_response

            providers = analyzer._get_resource_providers()

            assert providers == []

    def test_get_hypervisors_success(
        self, mock_environment_variables, sample_openstack_hypervisors
    ):
        """Test successful hypervisors retrieval."""
        analyzer = MAASCPUAnalyzer()

        with patch.object(
            analyzer, "_get_service_endpoint", return_value="http://test:8774"
        ):
            with patch.object(
                analyzer, "_get_openstack_token", return_value="test-token"
            ):
                with patch("requests.Session") as mock_session_class:
                    mock_session = Mock()
                    mock_session_class.return_value = mock_session

                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "hypervisors": sample_openstack_hypervisors
                    }
                    mock_session.get.return_value = mock_response

                    hypervisors = analyzer._get_hypervisors()

                    assert hypervisors == sample_openstack_hypervisors

    def test_get_hypervisors_no_nova_endpoint(self, mock_environment_variables):
        """Test hypervisors retrieval when Nova endpoint is not found."""
        analyzer = MAASCPUAnalyzer()

        with patch.object(analyzer, "_get_service_endpoint", return_value=None):
            hypervisors = analyzer._get_hypervisors()

            assert hypervisors == []

    def test_get_hypervisors_no_token(self, mock_environment_variables):
        """Test hypervisors retrieval when no authentication token is available."""
        analyzer = MAASCPUAnalyzer()

        with patch.object(
            analyzer, "_get_service_endpoint", return_value="http://test:8774"
        ):
            with patch.object(analyzer, "_get_openstack_token", return_value=None):
                hypervisors = analyzer._get_hypervisors()

                assert hypervisors == []

    def test_check_openstack_connectivity_success(self, mock_environment_variables):
        """Test successful OpenStack connectivity check."""
        analyzer = MAASCPUAnalyzer()

        with patch.object(analyzer, "_get_openstack_token", return_value="test-token"):
            with patch.object(
                analyzer, "_get_placement_endpoint", return_value="http://test:8778"
            ):
                result = analyzer._check_openstack_connectivity()

                assert result is True

    def test_check_openstack_connectivity_no_token(self, mock_environment_variables):
        """Test OpenStack connectivity check with no authentication token."""
        analyzer = MAASCPUAnalyzer()

        with patch.object(analyzer, "_get_openstack_token", return_value=None):
            result = analyzer._check_openstack_connectivity()

            assert result is False

    def test_check_openstack_connectivity_no_endpoint(self, mock_environment_variables):
        """Test OpenStack connectivity check with no placement endpoint."""
        analyzer = MAASCPUAnalyzer()

        with patch.object(analyzer, "_get_openstack_token", return_value="test-token"):
            with patch.object(analyzer, "_get_placement_endpoint", return_value=None):
                result = analyzer._check_openstack_connectivity()

                assert result is False

    def test_make_placement_api_request_success(self, mock_environment_variables):
        """Test successful placement API request."""
        analyzer = MAASCPUAnalyzer()

        with patch.object(
            analyzer, "_get_placement_endpoint", return_value="http://test:8778"
        ):
            with patch.object(
                analyzer, "_get_openstack_token", return_value="test-token"
            ):
                with patch("requests.Session") as mock_session_class:
                    mock_session = Mock()
                    mock_session_class.return_value = mock_session

                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.text = "Success"
                    mock_session.request.return_value = mock_response

                    response = analyzer._make_placement_api_request("GET", "/test")

                    assert response == mock_response
                    mock_session.request.assert_called_once()

    def test_make_placement_api_request_no_endpoint(self, mock_environment_variables):
        """Test placement API request with no endpoint."""
        analyzer = MAASCPUAnalyzer()

        with patch.object(analyzer, "_get_placement_endpoint", return_value=None):
            with pytest.raises(
                ValueError, match="Could not determine placement service endpoint"
            ):
                analyzer._make_placement_api_request("GET", "/test")

    def test_make_placement_api_request_no_token(self, mock_environment_variables):
        """Test placement API request with no authentication token."""
        analyzer = MAASCPUAnalyzer()

        with patch.object(
            analyzer, "_get_placement_endpoint", return_value="http://test:8778"
        ):
            with patch.object(analyzer, "_get_openstack_token", return_value=None):
                with pytest.raises(
                    ValueError, match="Could not obtain OpenStack authentication token"
                ):
                    analyzer._make_placement_api_request("GET", "/test")
