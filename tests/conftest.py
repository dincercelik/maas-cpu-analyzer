"""Pytest configuration and shared fixtures."""

import json
import os
from typing import Any, Dict, List
from unittest.mock import Mock, patch

import pytest


@pytest.fixture
def sample_maas_machines():
    """Sample MAAS machine data for testing."""
    return [
        {
            "hostname": "test-machine-1",
            "status_name": "Deployed",
            "zone": {"name": "zone-1"},
            "hardware_info": {"cpu_model": "Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz"},
            "tag_names": ["compute", "gpu"],
        },
        {
            "hostname": "test-machine-2",
            "status_name": "Deployed",
            "zone": {"name": "zone-1"},
            "hardware_info": {"cpu_model": "AMD EPYC 7551P 32-Core Processor"},
            "tag_names": ["compute"],
        },
        {
            "hostname": "test-machine-3",
            "status_name": "Ready",
            "zone": {"name": "zone-2"},
            "hardware_info": {"cpu_model": "Intel(R) Core(TM) i7-8700K CPU @ 3.70GHz"},
            "tag_names": ["storage"],
        },
        {
            "hostname": "test-machine-4",
            "status_name": "Deployed",
            "zone": {"name": "zone-1"},
            "hardware_info": {"cpu_model": "Unknown CPU Model"},
            "tag_names": [],
        },
    ]


@pytest.fixture
def sample_openstack_hypervisors():
    """Sample OpenStack hypervisor data for testing."""
    return [
        {
            "hypervisor_hostname": "test-machine-1",
            "name": "test-machine-1",
            "id": 1,
            "state": "up",
            "status": "enabled",
        },
        {
            "hypervisor_hostname": "test-machine-2",
            "name": "test-machine-2",
            "id": 2,
            "state": "up",
            "status": "enabled",
        },
    ]


@pytest.fixture
def sample_resource_providers():
    """Sample OpenStack resource provider data for testing."""
    return [
        {
            "uuid": "12345678-1234-1234-1234-123456789abc",
            "name": "test-machine-1",
            "generation": 1,
        },
        {
            "uuid": "87654321-4321-4321-4321-cba987654321",
            "name": "test-machine-2",
            "generation": 1,
        },
    ]


@pytest.fixture
def sample_traits():
    """Sample OpenStack traits data for testing."""
    return [
        "CUSTOM_INTEL_XEON_E5_2680_V4",
        "CUSTOM_AMD_EPYC_7551P_32_CORE",
        "CUSTOM_INTEL_CORE_I7_8700K",
    ]


@pytest.fixture
def mock_environment_variables():
    """Mock environment variables for testing."""
    env_vars = {
        "MAAS_URL": "http://test-maas:5240/MAAS",
        "MAAS_API_KEY": "test:key:secret",
        "OS_AUTH_URL": "http://test-openstack:5000/v3",
        "OS_USERNAME": "testuser",
        "OS_PASSWORD": "testpass",
        "OS_PROJECT_NAME": "testproject",
        "OS_USER_DOMAIN_NAME": "Default",
        "OS_PROJECT_DOMAIN_NAME": "Default",
    }

    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def mock_requests_session():
    """Mock requests session for testing."""
    with patch("requests.Session") as mock_session:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.text = ""
        mock_response.headers = {}
        mock_response.raise_for_status.return_value = None

        mock_session.return_value.get.return_value = mock_response
        mock_session.return_value.post.return_value = mock_response
        mock_session.return_value.put.return_value = mock_response
        mock_session.return_value.delete.return_value = mock_response
        mock_session.return_value.request.return_value = mock_response

        yield mock_session


@pytest.fixture
def mock_openstack_token():
    """Mock OpenStack authentication token."""
    return "test-auth-token-12345"


@pytest.fixture
def mock_service_catalog():
    """Mock OpenStack service catalog."""
    return {
        "catalog": [
            {
                "name": "placement",
                "endpoints": [
                    {"interface": "public", "url": "http://test-openstack:8778"}
                ],
            },
            {
                "name": "nova",
                "endpoints": [
                    {"interface": "public", "url": "http://test-openstack:8774"}
                ],
            },
        ]
    }


@pytest.fixture
def analyzer_instance():
    """Create a MAASCPUAnalyzer instance for testing."""
    from maas_cpu_analyzer.maas_cpu_analyzer import MAASCPUAnalyzer

    return MAASCPUAnalyzer(verbose=True)


@pytest.fixture
def mock_maas_response(sample_maas_machines):
    """Mock MAAS API response."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample_maas_machines
    mock_response.text = json.dumps(sample_maas_machines)
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.raise_for_status.return_value = None
    return mock_response


@pytest.fixture
def mock_openstack_responses():
    """Mock various OpenStack API responses."""
    responses = {
        "auth": Mock(
            status_code=201,
            headers={"X-Subject-Token": "test-token-12345"},
            json=Mock(return_value={}),
        ),
        "catalog": Mock(
            status_code=200,
            json=Mock(
                return_value={
                    "catalog": [
                        {
                            "name": "placement",
                            "endpoints": [
                                {
                                    "interface": "public",
                                    "url": "http://test-openstack:8778",
                                }
                            ],
                        }
                    ]
                }
            ),
        ),
        "hypervisors": Mock(
            status_code=200,
            json=Mock(
                return_value={
                    "hypervisors": [
                        {
                            "hypervisor_hostname": "test-machine-1",
                            "name": "test-machine-1",
                            "id": 1,
                        }
                    ]
                }
            ),
        ),
        "resource_providers": Mock(
            status_code=200,
            json=Mock(
                return_value={
                    "resource_providers": [
                        {
                            "uuid": "12345678-1234-1234-1234-123456789abc",
                            "name": "test-machine-1",
                            "generation": 1,
                        }
                    ]
                }
            ),
        ),
        "traits": Mock(
            status_code=200,
            json=Mock(
                return_value={
                    "traits": [
                        "CUSTOM_INTEL_XEON_E5_2680_V4",
                        "CUSTOM_AMD_EPYC_7551P_32_CORE",
                    ]
                }
            ),
        ),
    }
    return responses


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables after each test."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)
