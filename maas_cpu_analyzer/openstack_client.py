"""
OpenStack client module for MAAS CPU Analyzer.

This module handles all OpenStack-related operations including:
- Authentication
- Service catalog management
- Resource provider operations
- Trait management
"""

import json
import os
import sys
from contextlib import suppress
from typing import Dict, List, Optional

import requests


class OpenStackClient:
    """OpenStack client for handling OpenStack API operations"""

    # Class constants
    HTTP_TIMEOUT = 30
    MAX_RETRIES = 3
    SUCCESS_HTTP_CODES = [200, 201, 202, 204]

    def __init__(self, verbose: bool = False):
        """Initialize OpenStack client"""
        self.verbose = verbose
        self._auth_token: Optional[str] = None
        self._placement_endpoint: Optional[str] = None
        self._service_catalog: Optional[Dict] = None
        self._service_endpoints: Dict[str, str] = {}
        self._session = None
        self._custom_trait_pattern = None  # Will be set by main class

    def set_custom_trait_pattern(self, pattern):
        """Set the custom trait pattern"""
        self._custom_trait_pattern = pattern

    def log(self, message: str) -> None:
        """Log message if verbose mode is enabled"""
        if self.verbose:
            print(f"[OpenStack] {message}")

    def _get_session(self):
        """Get or create HTTP session"""
        if self._session is None:
            self._session = requests.Session()
            with suppress(Exception):
                adapter = requests.adapters.HTTPAdapter(max_retries=self.MAX_RETRIES)
                self._session.mount("http://", adapter)
                self._session.mount("https://", adapter)
            with suppress(Exception):
                self._session.headers.update({"Content-Type": "application/json"})
        return self._session

    def _clear_cache(self) -> None:
        """Clear all cached data"""
        self._auth_token = None
        self._placement_endpoint = None
        self._service_catalog = None
        self._service_endpoints = {}

    def check_openstack_environment(self) -> None:
        """Check for required OpenStack environment variables"""
        required_vars = [
            "OS_AUTH_URL",
            "OS_USERNAME",
            "OS_PASSWORD",
            "OS_PROJECT_NAME",
        ]
        missing_vars = [var for var in required_vars if not os.environ.get(var)]

        if missing_vars:
            print(
                "Error: Missing required OpenStack environment variables:",
                file=sys.stderr,
            )
            for var in missing_vars:
                print(f"  {var}", file=sys.stderr)
            print("Please set the following environment variables:", file=sys.stderr)
            print("  export OS_AUTH_URL='your-auth-url'", file=sys.stderr)
            print("  export OS_USERNAME='your-username'", file=sys.stderr)
            print("  export OS_PASSWORD='your-password'", file=sys.stderr)
            print("  export OS_PROJECT_NAME='your-project'", file=sys.stderr)
            sys.exit(1)

    def _get_openstack_token(self) -> Optional[str]:
        """Get OpenStack authentication token using direct HTTP calls with caching"""
        # Return cached token if available
        if self._auth_token:
            return self._auth_token

        # Get environment variables
        env_vars = self._get_openstack_env_vars()

        # Prepare authentication data
        auth_data = self._prepare_auth_data(env_vars)

        # Make authentication request
        return self._make_auth_request(env_vars["auth_url"], auth_data)

    def _get_openstack_env_vars(self) -> Dict[str, str]:
        """Get OpenStack environment variables"""
        auth_url = os.environ.get("OS_AUTH_URL")
        username = os.environ.get("OS_USERNAME")
        password = os.environ.get("OS_PASSWORD")
        project_name = os.environ.get("OS_PROJECT_NAME")
        user_domain_name = os.environ.get("OS_USER_DOMAIN_NAME", "Default")
        project_domain_name = os.environ.get("OS_PROJECT_DOMAIN_NAME", "Default")

        if not all([auth_url, username, password, project_name]):
            raise ValueError("Missing required OpenStack environment variables")

        # At this point we know auth_url is not None due to the check above
        assert auth_url is not None

        return {
            "auth_url": auth_url or "",
            "username": username or "",
            "password": password or "",
            "project_name": project_name or "",
            "user_domain_name": user_domain_name or "",
            "project_domain_name": project_domain_name or "",
        }

    def _prepare_auth_data(self, env_vars: Dict[str, str]) -> Dict:
        """Prepare authentication data for v3.0 API"""
        return {
            "auth": {
                "identity": {
                    "methods": ["password"],
                    "password": {
                        "user": {
                            "name": env_vars["username"],
                            "domain": {"name": env_vars["user_domain_name"]},
                            "password": env_vars["password"],
                        }
                    },
                },
                "scope": {
                    "project": {
                        "name": env_vars["project_name"],
                        "domain": {"name": env_vars["project_domain_name"]},
                    }
                },
            }
        }

    def _make_auth_request(self, auth_url: str, auth_data: Dict) -> Optional[str]:
        """Make authentication request to OpenStack"""
        try:
            # Construct the authentication endpoint for v3.0 API
            auth_endpoint = self._build_auth_endpoint(auth_url)
            self.log(f"Using authentication endpoint: {auth_endpoint}")

            session = self._get_session()
            response = session.post(
                auth_endpoint,
                json=auth_data,
                timeout=self.HTTP_TIMEOUT,
            )

            return self._process_auth_response(response)

        except Exception as e:
            self.log(f"Error getting OpenStack token: {e}")
            return None

    def _build_auth_endpoint(self, auth_url: str) -> str:
        """Build authentication endpoint URL"""
        # Ensure the auth_url ends with /v3
        auth_url = auth_url.rstrip("/")
        if not auth_url.endswith("/v3"):
            auth_url = f"{auth_url}/v3"
        return f"{auth_url}/auth/tokens"

    def _process_auth_response(self, response) -> Optional[str]:
        """Process authentication response"""
        # v3.0 returns 201
        if response.status_code == 201:
            # Extract token from response headers
            token = response.headers.get("X-Subject-Token")
            if token:
                # Cache the token for reuse
                self._auth_token = token
                self.log("Successfully obtained OpenStack authentication token")
                return token
            self.log("No token found in response headers")
            return None
        self.log(f"Authentication failed: {response.status_code} - {response.text}")
        return None

    def _get_service_catalog(self) -> Optional[Dict]:
        """Get OpenStack service catalog with caching"""
        # Return cached catalog if available
        if self._service_catalog:
            return self._service_catalog

        auth_url = os.environ.get("OS_AUTH_URL")
        if not auth_url:
            return None

        # Get authentication token
        token = self._get_openstack_token()
        if not token:
            return None

        try:
            return self._fetch_service_catalog(auth_url, token)
        except Exception as e:
            self.log(f"Error discovering service catalog: {e}")
            return None

    def _fetch_service_catalog(self, auth_url: str, token: str) -> Optional[Dict]:
        """Fetch service catalog from OpenStack"""
        # Ensure auth_url has /v3 for catalog discovery
        auth_url = auth_url.rstrip("/")
        if not auth_url.endswith("/v3"):
            auth_url = f"{auth_url}/v3"

        # Try different catalog endpoints
        catalog_endpoints = [f"{auth_url}/auth/catalog"]
        session = self._get_session()

        for catalog_url in catalog_endpoints:
            catalog = self._try_catalog_endpoint(session, catalog_url, token)
            if catalog:
                return catalog

        self.log("Failed to retrieve service catalog from any endpoint")
        return None

    def _try_catalog_endpoint(
        self, session, catalog_url: str, token: str
    ) -> Optional[Dict]:
        """Try to fetch catalog from a specific endpoint"""
        try:
            response = self._make_catalog_request(session, catalog_url, token)
            return self._process_catalog_response(response, catalog_url)

        except requests.exceptions.Timeout:
            self.log(f"Timeout accessing catalog endpoint {catalog_url}")
            return None
        except requests.exceptions.ConnectionError as e:
            self.log(f"Connection error accessing catalog endpoint {catalog_url}: {e}")
            return None
        except Exception as e:
            self.log(f"Error accessing catalog endpoint {catalog_url}: {e}")
            return None

    def _make_catalog_request(self, session, catalog_url: str, token: str):
        """Make catalog request"""
        return session.get(
            catalog_url,
            headers={"X-Auth-Token": token},
            timeout=self.HTTP_TIMEOUT,
        )

    def _process_catalog_response(self, response, catalog_url: str) -> Optional[Dict]:
        """Process catalog response"""
        if response.status_code == 200:
            return self._process_successful_catalog_response(response, catalog_url)
        if response.status_code == 401:
            return self._handle_authentication_failure(catalog_url)
        self.log(
            f"Catalog endpoint {catalog_url} returned {response.status_code}: {response.text[:200]}"
        )
        return None

    def _process_successful_catalog_response(
        self, response, catalog_url: str
    ) -> Optional[Dict]:
        """Process successful catalog response"""
        try:
            catalog = response.json()
            # Validate catalog structure
            if not isinstance(catalog, dict) or "catalog" not in catalog:
                self.log(f"Invalid catalog structure from {catalog_url}")
                return None

            self._service_catalog = catalog
            self.log(f"Successfully retrieved service catalog from {catalog_url}")
            return catalog
        except json.JSONDecodeError as e:
            self.log(f"Failed to parse JSON from {catalog_url}: {e}")
            return None

    def _handle_authentication_failure(self, catalog_url: str) -> Optional[Dict]:
        """Handle authentication failure for catalog endpoint"""
        self.log(f"Authentication failed for catalog endpoint {catalog_url}")
        # Clear cached token as it might be invalid
        self._auth_token = None

    def _get_service_endpoint(
        self, service_name: str, interface: str = "public"
    ) -> Optional[str]:
        """Get service endpoint from cached catalog"""
        # Check cache first
        cache_key = f"{service_name}:{interface}"
        if cache_key in self._service_endpoints:
            return self._service_endpoints[cache_key]

        # Get service catalog
        catalog = self._get_service_catalog()
        if not catalog:
            return None

        try:
            return self._find_service_endpoint_in_catalog(
                catalog, service_name, interface, cache_key
            )
        except Exception as e:
            self.log(f"Error parsing service catalog for {service_name}: {e}")
            return None

    def _find_service_endpoint_in_catalog(
        self, catalog: Dict, service_name: str, interface: str, cache_key: str
    ) -> Optional[str]:
        """Find service endpoint in catalog"""
        services = catalog.get("catalog", [])
        if not services:
            self.log("No services found in catalog")
            return None

        # Find matching services
        matching_services = self._find_matching_services(services, service_name)
        if not matching_services:
            return None

        # Find the first matching endpoint
        return self._find_first_matching_endpoint(
            matching_services, interface, service_name, cache_key
        )

    def _find_matching_services(
        self, services: List[Dict], service_name: str
    ) -> List[Dict]:
        """Find services matching the service name"""
        matching_services = [
            service for service in services if service.get("name") == service_name
        ]

        if not matching_services:
            self.log(f"Service '{service_name}' not found in catalog")
            return []

        return matching_services

    def _find_first_matching_endpoint(
        self,
        matching_services: List[Dict],
        interface: str,
        service_name: str,
        cache_key: str,
    ) -> Optional[str]:
        """Find the first matching endpoint in services"""
        for service in matching_services:
            endpoint = self._find_matching_endpoint(service, interface)
            if endpoint:
                return self._cache_and_return_endpoint(
                    endpoint, service_name, cache_key
                )

        self.log(f"No {interface} endpoint found for service '{service_name}'")
        return None

    def _find_matching_endpoint(self, service: Dict, interface: str) -> Optional[str]:
        """Find matching endpoint in service"""
        endpoints = service.get("endpoints", [])
        for endpoint in endpoints:
            if endpoint.get("interface") == interface:
                url = endpoint.get("url")
                if url:
                    return url.rstrip("/")
        return None

    def _cache_and_return_endpoint(
        self, url: str, service_name: str, cache_key: str
    ) -> str:
        """Cache and return endpoint URL"""
        self._service_endpoints[cache_key] = url
        self.log(f"Found {service_name} endpoint: {url}")
        return url

    def _get_placement_endpoint(self) -> Optional[str]:
        """Get placement service endpoint from OpenStack service catalog with caching"""
        # Return cached endpoint if available
        if self._placement_endpoint:
            return self._placement_endpoint

        # Use the optimized service endpoint discovery
        endpoint = self._get_service_endpoint("placement", "public")
        if endpoint:
            self._placement_endpoint = endpoint
            return endpoint

        self.log("Placement service not found in service catalog")
        return None

    def make_placement_api_request(
        self, method: str, endpoint: str, data: Optional[Dict] = None
    ):
        """Make API request to OpenStack placement service"""
        # Validate prerequisites
        self._validate_placement_request_prerequisites()

        # Prepare request
        url, headers = self._prepare_placement_request(endpoint, data)

        # Make request
        response = self._execute_placement_request(method, url, headers, data)

        # Log response details
        self._log_placement_response(method, url, response)

        return response

    def _validate_placement_request_prerequisites(self) -> None:
        """Validate prerequisites for placement API request"""
        placement_endpoint = self._get_placement_endpoint()
        if not placement_endpoint:
            raise Exception("Placement service endpoint not available")

        token = self._get_openstack_token()
        if not token:
            raise Exception("OpenStack authentication token not available")

    def _prepare_placement_request(self, endpoint: str, data: Optional[Dict]) -> tuple:
        """Prepare URL and headers for placement API request"""
        placement_endpoint = self._get_placement_endpoint()
        url = f"{placement_endpoint}{endpoint}"

        token = self._get_openstack_token()
        headers = {"X-Auth-Token": token}
        if data:
            headers["Content-Type"] = "application/json"

        return url, headers

    def _execute_placement_request(
        self, method: str, url: str, headers: Dict, data: Optional[Dict]
    ):
        """Execute the placement API request"""
        session = self._get_session()
        method_upper = method.upper()

        if method_upper == "GET":
            return session.get(url, headers=headers, timeout=self.HTTP_TIMEOUT)
        if method_upper == "POST":
            return session.post(
                url, headers=headers, json=data, timeout=self.HTTP_TIMEOUT
            )
        if method_upper == "PUT":
            return session.put(
                url, headers=headers, json=data, timeout=self.HTTP_TIMEOUT
            )
        if method_upper == "DELETE":
            return session.delete(url, headers=headers, timeout=self.HTTP_TIMEOUT)

        raise ValueError(f"Unsupported HTTP method: {method}")

    def _log_placement_response(self, method: str, url: str, response) -> None:
        """Log placement API response details"""
        self.log(f"API request: {method} {url}")
        self.log(f"Response status: {response.status_code}")
        if response.status_code not in self.SUCCESS_HTTP_CODES:
            self.log(f"Response body: {response.text}")

    def check_openstack_connectivity(self) -> bool:
        """Check if OpenStack services are accessible"""
        try:
            # Try to get a token
            token = self._get_openstack_token()
            if not token:
                return False

            # Ensure placement endpoint is available
            endpoint = self._get_placement_endpoint()
            if not endpoint:
                return False

            return True

        except Exception as e:
            self.log(f"OpenStack connectivity check failed: {e}")
            return False

    def get_resource_providers(self) -> List[Dict]:
        """Get all resource providers using direct HTTP calls"""
        endpoint = "/resource_providers"

        try:
            response = self.make_placement_api_request("GET", endpoint)

            if response.status_code in self.SUCCESS_HTTP_CODES:
                data = response.json()
                return data.get("resource_providers", [])
            self.log(
                f"Failed to get resource providers: {response.status_code} - {response.text}"
            )
            return []

        except Exception as e:
            self.log(f"Error getting resource providers: {e}")
            return []

    def get_resource_provider_traits(self, resource_provider_id: str) -> List[str]:
        """Get traits for a specific resource provider"""
        endpoint = f"/resource_providers/{resource_provider_id}/traits"

        try:
            response = self.make_placement_api_request("GET", endpoint)

            if response.status_code in self.SUCCESS_HTTP_CODES:
                current_traits_data = response.json()
                return current_traits_data.get("traits", [])
            self.log(
                f"Failed to get traits for resource provider {resource_provider_id}: {response.status_code} - {response.text}"
            )
            return []

        except Exception as e:
            self.log(f"Error getting current traits: {e}")
            return []

    def set_resource_provider_traits(
        self, resource_provider_id: str, trait_names: List[str]
    ) -> bool:
        """Set traits for a resource provider using the placement API"""
        endpoint = f"/resource_providers/{resource_provider_id}/traits"

        # Retry logic for generation conflicts
        for attempt in range(self.MAX_RETRIES):
            result = self._attempt_trait_setting(
                resource_provider_id, endpoint, trait_names, attempt
            )
            if result is not None:
                return result

        return False

    def _attempt_trait_setting(
        self,
        resource_provider_id: str,
        endpoint: str,
        trait_names: List[str],
        attempt: int,
    ) -> Optional[bool]:
        """Attempt to set traits with retry logic"""
        # Get the current resource provider to obtain the generation (fresh each time)
        generation = self._get_resource_provider_generation(resource_provider_id)
        if generation is None:
            return False

        # Prepare data with required generation field
        data = {"traits": trait_names, "resource_provider_generation": generation}

        try:
            return self._execute_trait_setting_request(
                resource_provider_id, endpoint, data, attempt
            )
        except Exception as e:
            self.log(
                f"Error setting traits for resource provider {resource_provider_id}: {e}"
            )
            return False

    def _get_resource_provider_generation(
        self, resource_provider_id: str
    ) -> Optional[int]:
        """Get resource provider generation"""
        try:
            rp_response = self.make_placement_api_request(
                "GET", f"/resource_providers/{resource_provider_id}"
            )
            if rp_response.status_code not in self.SUCCESS_HTTP_CODES:
                self.log(
                    f"Failed to get resource provider info: {rp_response.status_code} - {rp_response.text}"
                )
                return None

            rp_data = rp_response.json()
            return rp_data.get("generation", 0)

        except Exception as e:
            self.log(f"Error getting resource provider generation: {e}")
            return None

    def _execute_trait_setting_request(
        self, resource_provider_id: str, endpoint: str, data: Dict, attempt: int
    ) -> Optional[bool]:
        """Execute the trait setting request"""
        response = self.make_placement_api_request("PUT", endpoint, data)

        if response.status_code in self.SUCCESS_HTTP_CODES:
            self.log(
                f"Successfully set traits for resource provider {resource_provider_id}"
            )
            return True
        if response.status_code == 409 and attempt < self.MAX_RETRIES - 1:
            # Generation conflict - retry with fresh generation
            self.log(
                f"Generation conflict (attempt {attempt + 1}/{self.MAX_RETRIES}), retrying..."
            )
            return None  # Continue retry
        self.log(f"Failed to set traits: {response.status_code} - {response.text}")
        return False

    def create_trait(self, trait_name: str) -> tuple[bool, str]:
        """Create a trait in the placement service

        Returns:
            tuple: (success: bool, status: str) where status is 'created', 'already_exists', or 'error'
        """
        endpoint = f"/traits/{trait_name}"

        try:
            response = self.make_placement_api_request("PUT", endpoint)
            return self._process_trait_creation_response(response, trait_name)

        except Exception as e:
            self.log(f"Error creating trait {trait_name}: {e}")
            return False, "error"

    def _process_trait_creation_response(
        self, response, trait_name: str
    ) -> tuple[bool, str]:
        """Process trait creation response"""
        if response.status_code in [200, 201]:
            self.log(f"Successfully created trait: {trait_name}")
            return True, "created"
        if response.status_code == 204:
            self.log(f"Trait {trait_name} already exists")
            return True, "already_exists"
        return self._handle_trait_creation_error(response, trait_name)

    def _handle_trait_creation_error(
        self, response, trait_name: str
    ) -> tuple[bool, str]:
        """Handle trait creation error response"""
        # Check if trait already exists
        error_msg = response.text.lower()
        if any(
            keyword in error_msg
            for keyword in ["already exists", "conflict", "duplicate", "409"]
        ):
            self.log(f"Trait {trait_name} already exists")
            return True, "already_exists"
        self.log(f"Failed to create trait: {response.status_code} - {response.text}")
        return False, "error"

    def get_hypervisors(self) -> List[Dict]:
        """Get all hypervisors from OpenStack Nova service"""
        # Get Nova endpoint
        nova_endpoint = self._get_service_endpoint("nova", "public")
        if not nova_endpoint:
            self.log("Nova service not found in service catalog")
            return []

        # Get authentication token
        token = self._get_openstack_token()
        if not token:
            self.log("OpenStack authentication token not available")
            return []

        try:
            # Construct hypervisors endpoint
            hypervisors_url = f"{nova_endpoint}/os-hypervisors/detail"

            # Make request
            session = self._get_session()
            response = session.get(
                hypervisors_url,
                headers={"X-Auth-Token": token},
                timeout=self.HTTP_TIMEOUT,
            )

            if response.status_code in self.SUCCESS_HTTP_CODES:
                data = response.json()
                return data.get("hypervisors", [])
            self.log(
                f"Failed to get hypervisors: {response.status_code} - {response.text}"
            )
            return []

        except Exception as e:
            self.log(f"Error getting hypervisors: {e}")
            return []
