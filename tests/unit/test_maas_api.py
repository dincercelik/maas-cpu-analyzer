"""Unit tests for MAAS API interactions."""

import json
from unittest.mock import Mock, patch

import pytest
import requests

from maas_cpu_analyzer.maas_cpu_analyzer import MAASCPUAnalyzer


class TestMAASAPI:
    """Test cases for MAAS API interactions."""

    def test_fetch_maas_data_success(
        self, mock_environment_variables, mock_maas_response
    ):
        """Test successful MAAS data fetching."""
        analyzer = MAASCPUAnalyzer()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            mock_session.get.return_value = mock_maas_response

            result = analyzer.fetch_maas_data()

            assert result == mock_maas_response.json.return_value
            mock_session.get.assert_called_once()

    def test_fetch_maas_data_missing_url(self, capsys):
        """Test MAAS data fetching with missing MAAS_URL."""
        analyzer = MAASCPUAnalyzer()

        with patch.dict("os.environ", {"MAAS_API_KEY": "test:key:secret"}, clear=True):
            with pytest.raises(SystemExit):
                analyzer.fetch_maas_data()

            captured = capsys.readouterr()
            assert (
                "MAAS_URL and MAAS_API_KEY environment variables must be set"
                in captured.err
            )

    def test_fetch_maas_data_missing_api_key(self, capsys):
        """Test MAAS data fetching with missing MAAS_API_KEY."""
        analyzer = MAASCPUAnalyzer()

        with patch.dict(
            "os.environ", {"MAAS_URL": "http://test:5240/MAAS"}, clear=True
        ):
            with pytest.raises(SystemExit):
                analyzer.fetch_maas_data()

            captured = capsys.readouterr()
            assert (
                "MAAS_URL and MAAS_API_KEY environment variables must be set"
                in captured.err
            )

    def test_fetch_maas_data_invalid_api_key_format(self, capsys):
        """Test MAAS data fetching with invalid API key format."""
        analyzer = MAASCPUAnalyzer()

        with patch.dict(
            "os.environ",
            {"MAAS_URL": "http://test:5240/MAAS", "MAAS_API_KEY": "invalid_format"},
            clear=True,
        ):
            with pytest.raises(SystemExit):
                analyzer.fetch_maas_data()

            captured = capsys.readouterr()
            assert "MAAS_API_KEY must be in format" in captured.err

    def test_fetch_maas_data_http_error(self, mock_environment_variables, capsys):
        """Test MAAS data fetching with HTTP error."""
        analyzer = MAASCPUAnalyzer()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Simulate HTTP error
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_response.headers = {"Content-Type": "text/plain"}
            mock_response.raise_for_status.side_effect = (
                requests.exceptions.RequestException("401 Unauthorized")
            )
            mock_session.get.return_value = mock_response

            with pytest.raises(SystemExit):
                analyzer.fetch_maas_data()

            captured = capsys.readouterr()
            assert "Failed to fetch MAAS data" in captured.err

    def test_fetch_maas_data_json_decode_error(
        self, mock_environment_variables, capsys
    ):
        """Test MAAS data fetching with JSON decode error."""
        analyzer = MAASCPUAnalyzer()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Simulate JSON decode error
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_response.headers = {"Content-Type": "application/json"}
            mock_response.raise_for_status.return_value = None
            mock_session.get.return_value = mock_response

            with pytest.raises(SystemExit):
                analyzer.fetch_maas_data()

            captured = capsys.readouterr()
            assert "Failed to parse MAAS JSON data" in captured.err

    def test_fetch_maas_data_oauth_configuration(self, mock_environment_variables):
        """Test OAuth configuration for MAAS API."""
        analyzer = MAASCPUAnalyzer()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_response.headers = {"Content-Type": "application/json"}
            mock_response.raise_for_status.return_value = None
            mock_session.get.return_value = mock_response

            analyzer.fetch_maas_data()

            # Verify OAuth1 was called with correct parameters
            mock_session.get.assert_called_once()
            call_args = mock_session.get.call_args
            assert "auth" in call_args.kwargs
            assert call_args.kwargs["timeout"] == 30

    def test_fetch_maas_data_api_url_construction(self, mock_environment_variables):
        """Test MAAS API URL construction."""
        analyzer = MAASCPUAnalyzer()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_response.headers = {"Content-Type": "application/json"}
            mock_response.raise_for_status.return_value = None
            mock_session.get.return_value = mock_response

            analyzer.fetch_maas_data()

            # Verify the API URL was constructed correctly
            call_args = mock_session.get.call_args
            expected_url = "http://test-maas:5240/MAAS/api/2.0/machines/"
            assert call_args.args[0] == expected_url

    def test_fetch_maas_data_with_trailing_slash(self):
        """Test MAAS API URL construction with trailing slash in MAAS_URL."""
        analyzer = MAASCPUAnalyzer()

        with patch.dict(
            "os.environ",
            {
                "MAAS_URL": "http://test-maas:5240/MAAS/",
                "MAAS_API_KEY": "test:key:secret",
            },
            clear=True,
        ):
            with patch("requests.Session") as mock_session_class:
                mock_session = Mock()
                mock_session_class.return_value = mock_session

                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = []
                mock_response.headers = {"Content-Type": "application/json"}
                mock_response.raise_for_status.return_value = None
                mock_session.get.return_value = mock_response

                analyzer.fetch_maas_data()

                # Verify the API URL was constructed correctly without double slash
                call_args = mock_session.get.call_args
                expected_url = "http://test-maas:5240/MAAS/api/2.0/machines/"
                assert call_args.args[0] == expected_url

    def test_fetch_maas_data_verbose_logging(self, mock_environment_variables, capsys):
        """Test verbose logging during MAAS data fetching."""
        analyzer = MAASCPUAnalyzer(verbose=True)

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_response.raise_for_status.return_value = None
            mock_response.headers = {"Content-Type": "application/json"}
            mock_session.get.return_value = mock_response

            analyzer.fetch_maas_data()

            captured = capsys.readouterr()
            assert "Making request to:" in captured.err
            assert "Response status: 200" in captured.err
            assert "Successfully fetched machine data" in captured.err

    def test_fetch_maas_data_error_response_logging(
        self, mock_environment_variables, capsys
    ):
        """Test error response logging during MAAS data fetching."""
        analyzer = MAASCPUAnalyzer(verbose=True)

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_response.headers = {"Content-Type": "text/plain"}
            mock_response.raise_for_status.side_effect = (
                requests.exceptions.RequestException("500 Internal Server Error")
            )
            mock_session.get.return_value = mock_response

            with pytest.raises(SystemExit):
                analyzer.fetch_maas_data()

            captured = capsys.readouterr()
            assert "Response status: 500" in captured.err
            assert "Response body: Internal Server Error" in captured.err
