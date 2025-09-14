#!/usr/bin/env python3
"""
MAAS CPU Analyzer - Analyze CPU models in MAAS machines and optionally create OpenStack traits for resource scheduling

This tool analyzes CPU models in MAAS machines and optionally creates OpenStack traits for resource scheduling and placement optimization.
"""

import argparse
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime
from typing import Dict, List, Optional

import requests
from prettytable import PrettyTable
from requests_oauthlib import OAuth1


class MAASCPUAnalyzer:
    """Main class for MAAS CPU analysis"""

    # Compiled regex patterns for better performance
    _INTEL_AMD_PATTERN = re.compile(r"(?i)(intel|amd)")
    _CPU_PROCESSOR_PATTERN = re.compile(r"\s+(CPU|PROCESSOR)$")
    _SPECIAL_CHARS_PATTERN = re.compile(r"[^A-Z0-9]")
    _MULTIPLE_UNDERSCORES_PATTERN = re.compile(r"_+")
    _CUSTOM_TRAIT_PATTERN = re.compile(r"^CUSTOM_")

    # Constants
    PLACEMENT_API_VERSION = "1.6"
    HTTP_TIMEOUT = 30
    SUCCESS_HTTP_CODES = [200, 201, 204]
    MAX_RETRIES = 3
    BACKOFF_FACTOR = 0.1

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self._log_prefix = None
        # Cache for authentication token and endpoints
        self._auth_token = None
        self._placement_endpoint = None
        self._session = None
        # Cache for service catalog and endpoints
        self._service_catalog = None
        self._service_endpoints = {}

    def _get_log_prefix(self) -> str:
        """Get cached log prefix with timestamp"""
        if self._log_prefix is None:
            self._log_prefix = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"
        return self._log_prefix

    def log(self, message: str) -> None:
        """Log message if verbose mode is enabled"""
        if self.verbose:
            print(f"{self._get_log_prefix()} {message}", file=sys.stderr)

    def _handle_error(self, error: Exception, context: str, return_value=None) -> None:
        """Handle common error patterns with consistent logging"""
        self.log(f"Error {context}: {error}")
        if return_value is not None:
            return return_value

    def _get_session(self) -> requests.Session:
        """Get or create a requests session for connection reuse"""
        if self._session is None:
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry

            self._session = requests.Session()

            # Configure connection pooling and retries
            retry_strategy = Retry(
                total=self.MAX_RETRIES,
                backoff_factor=self.BACKOFF_FACTOR,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = HTTPAdapter(
                max_retries=retry_strategy, pool_connections=10, pool_maxsize=20
            )
            self._session.mount("http://", adapter)
            self._session.mount("https://", adapter)

            # Set default headers for all requests
            self._session.headers.update(
                {
                    "Content-Type": "application/json",
                    "User-Agent": "MAAS-CPU-Analyzer/1.0",
                    "Connection": "keep-alive",
                }
            )
        return self._session

    def _clear_cache(self) -> None:
        """Clear cached authentication token and endpoints"""
        self._auth_token = None
        self._placement_endpoint = None
        self._service_catalog = None
        self._service_endpoints.clear()
        if self._session:
            self._session.close()
            self._session = None

    def _make_placement_api_request(
        self, method: str, endpoint: str, data: Optional[Dict] = None
    ) -> requests.Response:
        """Make an authenticated HTTP request to the placement API"""
        # Get the placement endpoint
        placement_endpoint = self._get_placement_endpoint()
        if not placement_endpoint:
            raise ValueError("Could not determine placement service endpoint")

        url = f"{placement_endpoint}{endpoint}"

        # Get authentication token
        auth_token = self._get_openstack_token()
        if not auth_token:
            raise ValueError("Could not obtain OpenStack authentication token")

        # Prepare request headers
        headers = {
            "X-Auth-Token": auth_token,
            "OpenStack-API-Version": f"placement {self.PLACEMENT_API_VERSION}",
        }

        self.log(f"Making {method} request to: {url}")
        if data:
            self.log(f"Request data: {data}")

        # Make the HTTP request using session
        session = self._get_session()
        response = session.request(
            method=method,
            url=url,
            json=data,
            headers=headers,
            timeout=self.HTTP_TIMEOUT,
        )

        self.log(f"Response status: {response.status_code}")
        if response.status_code not in self.SUCCESS_HTTP_CODES:
            self.log(f"Response body: {response.text}")

        return response

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
            # Ensure auth_url has /v3 for catalog discovery
            auth_url = auth_url.rstrip("/")
            if not auth_url.endswith("/v3"):
                auth_url = f"{auth_url}/v3"

            # Try different catalog endpoints
            catalog_endpoints = [f"{auth_url}/auth/catalog"]

            session = self._get_session()
            for catalog_url in catalog_endpoints:
                try:
                    response = session.get(
                        catalog_url,
                        headers={"X-Auth-Token": token},
                        timeout=self.HTTP_TIMEOUT,
                    )

                    if response.status_code == 200:
                        try:
                            catalog = response.json()
                            # Validate catalog structure
                            if (
                                not isinstance(catalog, dict)
                                or "catalog" not in catalog
                            ):
                                self.log(
                                    f"Invalid catalog structure from {catalog_url}"
                                )
                                continue

                            self._service_catalog = catalog
                            self.log(
                                f"Successfully retrieved service catalog from {catalog_url}"
                            )
                            return catalog
                        except json.JSONDecodeError as e:
                            self.log(f"Failed to parse JSON from {catalog_url}: {e}")
                            continue
                    elif response.status_code == 401:
                        self.log(
                            f"Authentication failed for catalog endpoint {catalog_url}"
                        )
                        # Clear cached token as it might be invalid
                        self._auth_token = None
                        return None
                    else:
                        self.log(
                            f"Catalog endpoint {catalog_url} returned {response.status_code}: {response.text[:200]}"
                        )

                except requests.exceptions.Timeout:
                    self.log(f"Timeout accessing catalog endpoint {catalog_url}")
                    continue
                except requests.exceptions.ConnectionError as e:
                    self.log(
                        f"Connection error accessing catalog endpoint {catalog_url}: {e}"
                    )
                    continue
                except Exception as e:
                    self.log(f"Error accessing catalog endpoint {catalog_url}: {e}")
                    continue

            self.log("Failed to retrieve service catalog from any endpoint")
            return None

        except Exception as e:
            self.log(f"Error discovering service catalog: {e}")
            return None

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
            # Parse catalog to find service endpoint with optimized lookup
            services = catalog.get("catalog", [])
            if not services:
                self.log(f"No services found in catalog")
                return None

            # Use list comprehension for faster lookup
            matching_services = [
                service for service in services if service.get("name") == service_name
            ]

            if not matching_services:
                self.log(f"Service '{service_name}' not found in catalog")
                return None

            # Find the first matching endpoint
            for service in matching_services:
                endpoints = service.get("endpoints", [])
                for endpoint in endpoints:
                    if endpoint.get("interface") == interface:
                        url = endpoint.get("url")
                        if url:
                            # Cache the endpoint
                            self._service_endpoints[cache_key] = url.rstrip("/")
                            self.log(
                                f"Found {service_name} endpoint: {self._service_endpoints[cache_key]}"
                            )
                            return self._service_endpoints[cache_key]

            self.log(f"No {interface} endpoint found for service '{service_name}'")
            return None

        except Exception as e:
            self.log(f"Error parsing service catalog for {service_name}: {e}")
            return None

    def _set_resource_provider_traits(
        self, resource_provider_id: str, trait_names: List[str]
    ) -> bool:
        """Set traits for a resource provider using the placement API"""
        endpoint = f"/resource_providers/{resource_provider_id}/traits"

        # Retry logic for generation conflicts
        for attempt in range(self.MAX_RETRIES):
            # Get the current resource provider to obtain the generation (fresh each time)
            try:
                rp_response = self._make_placement_api_request(
                    "GET", f"/resource_providers/{resource_provider_id}"
                )
                if rp_response.status_code not in self.SUCCESS_HTTP_CODES:
                    self.log(
                        f"Failed to get resource provider info: {rp_response.status_code} - {rp_response.text}"
                    )
                    return False

                rp_data = rp_response.json()
                generation = rp_data.get("generation", 0)

            except Exception as e:
                return self._handle_error(
                    e, "getting resource provider generation", False
                )

            # Prepare data with required generation field
            data = {"traits": trait_names, "resource_provider_generation": generation}

            try:
                response = self._make_placement_api_request("PUT", endpoint, data)

                if response.status_code in self.SUCCESS_HTTP_CODES:
                    self.log(
                        f"Successfully set traits for resource provider {resource_provider_id}"
                    )
                    return True
                elif response.status_code == 409 and attempt < self.MAX_RETRIES - 1:
                    # Generation conflict - retry with fresh generation
                    self.log(
                        f"Generation conflict (attempt {attempt + 1}/{self.MAX_RETRIES}), retrying..."
                    )
                    continue
                else:
                    self.log(
                        f"Failed to set traits: {response.status_code} - {response.text}"
                    )
                    return False

            except Exception as e:
                return self._handle_error(
                    e,
                    f"setting traits for resource provider {resource_provider_id}",
                    False,
                )

        return False

    def _get_resource_provider_traits(self, resource_provider_id: str) -> List[str]:
        """Get traits for a specific resource provider"""
        endpoint = f"/resource_providers/{resource_provider_id}/traits"

        try:
            response = self._make_placement_api_request("GET", endpoint)

            if response.status_code in self.SUCCESS_HTTP_CODES:
                current_traits_data = response.json()
                return current_traits_data.get("traits", [])
            else:
                self.log(
                    f"Failed to get current traits: {response.status_code} - {response.text}"
                )
                return []

        except Exception as e:
            return self._handle_error(e, "getting current traits", [])

    def _get_openstack_token(self) -> Optional[str]:
        """Get OpenStack authentication token using direct HTTP calls with caching"""
        # Return cached token if available
        if self._auth_token:
            return self._auth_token

        auth_url = os.environ.get("OS_AUTH_URL")
        username = os.environ.get("OS_USERNAME")
        password = os.environ.get("OS_PASSWORD")
        project_name = os.environ.get("OS_PROJECT_NAME")
        user_domain_name = os.environ.get("OS_USER_DOMAIN_NAME", "Default")
        project_domain_name = os.environ.get("OS_PROJECT_DOMAIN_NAME", "Default")

        if not all([auth_url, username, password, project_name]):
            raise ValueError("Missing required OpenStack environment variables")

        # Prepare authentication data for v3.0 API
        auth_data = {
            "auth": {
                "identity": {
                    "methods": ["password"],
                    "password": {
                        "user": {
                            "name": username,
                            "domain": {"name": user_domain_name},
                            "password": password,
                        }
                    },
                },
                "scope": {
                    "project": {
                        "name": project_name,
                        "domain": {"name": project_domain_name},
                    }
                },
            }
        }

        try:
            # Construct the authentication endpoint for v3.0 API
            # Ensure the auth_url ends with /v3
            auth_url = auth_url.rstrip("/")
            if not auth_url.endswith("/v3"):
                auth_url = f"{auth_url}/v3"

            auth_endpoint = f"{auth_url}/auth/tokens"
            self.log(f"Using authentication endpoint: {auth_endpoint}")

            session = self._get_session()
            response = session.post(
                auth_endpoint,
                json=auth_data,
                timeout=self.HTTP_TIMEOUT,
            )

            # v3.0 returns 201
            if response.status_code == 201:
                # Extract token from response headers
                token = response.headers.get("X-Subject-Token")
                if token:
                    # Cache the token for reuse
                    self._auth_token = token
                    self.log("Successfully obtained OpenStack authentication token")
                    return token
                else:
                    self.log("No token found in response headers")
                    return None
            else:
                self.log(
                    f"Authentication failed: {response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            return self._handle_error(e, "getting OpenStack token", None)

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

    def _get_resource_providers(self) -> List[Dict]:
        """Get all resource providers using direct HTTP calls"""
        endpoint = "/resource_providers"

        try:
            response = self._make_placement_api_request("GET", endpoint)

            if response.status_code in self.SUCCESS_HTTP_CODES:
                data = response.json()
                return data.get("resource_providers", [])
            else:
                self.log(
                    f"Failed to get resource providers: {response.status_code} - {response.text}"
                )
                return []

        except Exception as e:
            self.log(f"Error getting resource providers: {e}")
            return []

    def _get_hypervisors(self) -> List[Dict]:
        """Get all hypervisors using direct HTTP calls to Nova API"""
        # Get Nova endpoint using optimized discovery
        nova_url = self._get_service_endpoint("nova", "public")
        if not nova_url:
            self.log("Nova service not found")
            return []

        # Get hypervisors from Nova API
        token = self._get_openstack_token()
        if not token:
            return []

        try:
            session = self._get_session()
            response = session.get(
                f"{nova_url}/os-hypervisors",
                headers={"X-Auth-Token": token},
                timeout=self.HTTP_TIMEOUT,
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("hypervisors", [])
            else:
                self.log(
                    f"Failed to get hypervisors: {response.status_code} - {response.text}"
                )
                return []

        except Exception as e:
            self.log(f"Error getting hypervisors: {e}")
            return []

    def _check_openstack_connectivity(self) -> bool:
        """Check if we can connect to OpenStack services"""
        try:
            # Test authentication
            token = self._get_openstack_token()
            if not token:
                return False

            # Test placement endpoint
            endpoint = self._get_placement_endpoint()
            if not endpoint:
                return False

            self.log("OpenStack connectivity check passed")
            return True

        except Exception as e:
            self.log(f"OpenStack connectivity check failed: {e}")
            return False

    def _create_trait(self, trait_name: str) -> tuple[bool, str]:
        """Create a trait in the placement service

        Returns:
            tuple: (success: bool, status: str) where status is 'created', 'already_exists', or 'error'
        """
        endpoint = f"/traits/{trait_name}"

        try:
            response = self._make_placement_api_request("PUT", endpoint)

            if response.status_code == 201:
                self.log(f"Successfully created trait: {trait_name}")
                return True, "created"
            elif response.status_code == 204:
                self.log(f"Trait {trait_name} already exists")
                return True, "already_exists"
            elif response.status_code in [200]:
                self.log(f"Successfully created trait: {trait_name}")
                return True, "created"
            else:
                # Check if trait already exists
                error_msg = response.text.lower()
                if any(
                    keyword in error_msg
                    for keyword in ["already exists", "conflict", "duplicate", "409"]
                ):
                    self.log(f"Trait {trait_name} already exists")
                    return True, "already_exists"
                else:
                    self.log(
                        f"Failed to create trait: {response.status_code} - {response.text}"
                    )
                    return False, "error"

        except Exception as e:
            self.log(f"Error creating trait {trait_name}: {e}")
            return False, "error"

    def check_dependencies(self) -> None:
        """Check if required Python libraries are available"""
        # Dependencies are now imported at module level
        # This method is kept for compatibility but no longer needed
        pass

    def fetch_maas_data(self) -> List[Dict]:
        """Fetch machine data from MAAS API"""
        self.log("Fetching machine data from MAAS...")

        # Get MAAS configuration from environment
        maas_url = os.environ.get("MAAS_URL")
        maas_api_key = os.environ.get("MAAS_API_KEY")

        if not maas_url or not maas_api_key:
            print(
                "Error: MAAS_URL and MAAS_API_KEY environment variables must be set",
                file=sys.stderr,
            )
            sys.exit(1)

        # Parse API key (format: consumer_key:token_key:token_secret)
        api_key_parts = maas_api_key.split(":")
        if len(api_key_parts) != 3:
            print(
                "Error: MAAS_API_KEY must be in format 'consumer_key:token_key:token_secret'",
                file=sys.stderr,
            )
            sys.exit(1)

        consumer_key, token_key, token_secret = api_key_parts

        # Configure OAuth 1.0a for MAAS API authentication
        auth = OAuth1(
            consumer_key,
            client_secret="",  # MAAS doesn't use client secret
            resource_owner_key=token_key,
            resource_owner_secret=token_secret,
            signature_method="PLAINTEXT",
            signature_type="AUTH_HEADER",
        )

        # Construct API URL
        api_url = f"{maas_url.rstrip('/')}/api/2.0/machines/"

        try:
            self.log(f"Making request to: {api_url}")
            session = self._get_session()
            response = session.get(api_url, auth=auth, timeout=30)

            self.log(f"Response status: {response.status_code}")
            self.log(f"Response headers: {dict(response.headers)}")
            if response.status_code != 200:
                self.log(f"Response body: {response.text}")

            response.raise_for_status()

            data = response.json()
            self.log("Successfully fetched machine data")
            return data
        except requests.exceptions.RequestException as e:
            print(f"Error: Failed to fetch MAAS data: {e}", file=sys.stderr)
            if hasattr(e, "response") and e.response is not None:
                if self.verbose:
                    print(f"Response status: {e.response.status_code}", file=sys.stderr)
                    print(f"Response body: {e.response.text}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Failed to parse MAAS JSON data: {e}", file=sys.stderr)
            sys.exit(1)

    def filter_machines(
        self,
        machines: List[Dict],
        zone: Optional[str],
        deployed_only: bool,
        tags: List[str],
    ) -> List[Dict]:
        """Filter machines based on zone, deployment status, and tags"""
        if not machines:
            return []

        # Convert tags to set for O(1) lookup
        tags_set = set(tags) if tags else set()

        def should_include_machine(machine: Dict) -> bool:
            # Filter by zone
            if zone and machine.get("zone", {}).get("name") != zone:
                return False

            # Filter by deployment status
            if deployed_only and machine.get("status_name") != "Deployed":
                return False

            # Filter by tags
            if tags_set:
                machine_tags = machine.get("tag_names", [])
                # Handle both string and object tag formats
                if machine_tags and isinstance(machine_tags[0], dict):
                    machine_tags = [tag.get("name", "") for tag in machine_tags]
                # Convert to set for efficient intersection check
                machine_tags_set = set(machine_tags)
                if not tags_set.intersection(machine_tags_set):
                    return False

            return True

        return [machine for machine in machines if should_include_machine(machine)]

    def get_cpu_vendor(self, cpu_model: str) -> str:
        """Extract CPU vendor from model name"""
        if not cpu_model:
            return "UNKNOWN"

        match = self._INTEL_AMD_PATTERN.search(cpu_model)
        if match:
            return match.group(1).upper()
            return "UNKNOWN"

    def generate_trait_name(self, cpu_model: str) -> str:
        """Generate OpenStack trait name from CPU model

        Converts CPU model names to OpenStack-compatible trait names by:
        - Converting to uppercase
        - Removing CPU/Processor suffixes
        - Replacing special characters with underscores
        - Adding CUSTOM_ prefix for vendor identification
        """
        if not cpu_model:
            return "CUSTOM_UNKNOWN_EMPTY"

        cpu_upper = cpu_model.upper()

        # Remove CPU/Processor suffixes using compiled pattern
        cpu_clean = self._CPU_PROCESSOR_PATTERN.sub("", cpu_upper)

        # Replace special characters with underscores using compiled pattern
        cpu_clean = self._SPECIAL_CHARS_PATTERN.sub("_", cpu_clean)

        # Remove multiple underscores using compiled pattern
        cpu_clean = self._MULTIPLE_UNDERSCORES_PATTERN.sub("_", cpu_clean)

        # Remove leading/trailing underscores
        cpu_clean = cpu_clean.strip("_")

        # Add CUSTOM prefix based on vendor
        if "INTEL" in cpu_clean:
            return f"CUSTOM_{cpu_clean}"
        elif "AMD" in cpu_clean:
            return f"CUSTOM_{cpu_clean}"
        else:
            return f"CUSTOM_UNKNOWN_{cpu_clean}"

    def print_table(self, columns: List[str], rows: List[List[str]]) -> None:
        """Print table using PrettyTable with left alignment"""
        table = PrettyTable()
        table.field_names = columns
        # Set left alignment for all columns
        table.align = "l"
        for row in rows:
            table.add_row(row)
        print(table)

    def print_machine_table(
        self, machines: List[Dict], zone: str, deployed_only: bool
    ) -> None:
        """Print the main machine table using PrettyTable"""
        filtered_machines = self.filter_machines(
            machines, zone, deployed_only, self.tags
        )

        # Filter for Intel/AMD CPUs only using compiled pattern
        cpu_machines = []
        for machine in filtered_machines:
            cpu_model = machine.get("hardware_info", {}).get("cpu_model", "")
            if self._INTEL_AMD_PATTERN.search(cpu_model):
                cpu_machines.append(machine)

        if not cpu_machines:
            zone_msg = f" in zone: {zone}" if zone else ""
            print(f"No machines found with Intel or AMD CPUs{zone_msg}.")
            return

        status_msg = "deployed" if deployed_only else "all"
        tags_msg = f" with tags: {', '.join(self.tags)}" if self.tags else ""
        zone_msg = f" in zone: {zone}" if zone else " (all zones)"
        print(f"Processing {status_msg} machines{zone_msg}{tags_msg}")

        if self.should_create_openstack_traits:
            columns = [
                "Hostname",
                "Zone",
                "Status",
                "Vendor",
                "CPU Model",
                "OpenStack Trait",
            ]
        else:
            columns = ["Hostname", "Zone", "Status", "Vendor", "CPU Model"]

        rows = []
        for machine in cpu_machines:
            hostname = machine.get("hostname", "unknown")
            machine_zone = machine.get("zone", {}).get("name", "unknown")
            status = machine.get("status_name", "unknown")
            cpu_model = machine.get("hardware_info", {}).get("cpu_model", "")
            vendor = self.get_cpu_vendor(cpu_model)

            if self.should_create_openstack_traits:
                trait_name = self.generate_trait_name(cpu_model)
                rows.append(
                    [hostname, machine_zone, status, vendor, cpu_model, trait_name]
                )
            else:
                rows.append([hostname, machine_zone, status, vendor, cpu_model])

        self.print_table(columns, rows)

    def print_cpu_distribution(
        self, machines: List[Dict], zone: str, deployed_only: bool
    ) -> None:
        """Print CPU model distribution using PrettyTable"""
        print()
        self.log("Generating CPU model histogram")

        filtered_machines = self.filter_machines(
            machines, zone, deployed_only, self.tags
        )
        cpu_models = []

        for machine in filtered_machines:
            cpu_model = machine.get("hardware_info", {}).get("cpu_model", "")
            if self._INTEL_AMD_PATTERN.search(cpu_model):
                cpu_models.append(cpu_model)

        if not cpu_models:
            return

        # Use Counter for efficient counting
        model_counts = Counter(cpu_models)
        sorted_models = model_counts.most_common()

        status_text = "Deployed Machines Only" if deployed_only else "All Machines"
        zone_text = f" in {zone}" if zone else " (All Zones)"
        title = f"CPU Model Distribution ({status_text}{zone_text})"
        print(title)

        columns = ["Count", "CPU Model"]
        rows = [[str(count), model] for model, count in sorted_models]

        self.print_table(columns, rows)

    def check_openstack_environment(self):
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
                print(f"  - {var}", file=sys.stderr)
            print(
                "\nPlease set the following environment variables for OpenStack operations:",
                file=sys.stderr,
            )
            print(
                "  export OS_AUTH_URL='http://your-openstack:5000/v3'", file=sys.stderr
            )
            print("  export OS_USERNAME='your-username'", file=sys.stderr)
            print("  export OS_PASSWORD='your-password'", file=sys.stderr)
            print("  export OS_PROJECT_NAME='your-project'", file=sys.stderr)
            sys.exit(1)

    def create_openstack_traits(
        self, machines: List[Dict], zone: str, deployed_only: bool
    ) -> None:
        """Create OpenStack traits from CPU models"""
        if not self.should_create_openstack_traits:
            return

        print()
        self.log("Generating and creating OpenStack trait names")
        print("Creating OpenStack Traits")

        # Get unique CPU models and generate trait names
        filtered_machines = self.filter_machines(
            machines, zone, deployed_only, self.tags
        )

        trait_names = {
            self.generate_trait_name(
                machine.get("hardware_info", {}).get("cpu_model", "")
            )
            for machine in filtered_machines
            if self._INTEL_AMD_PATTERN.search(
                machine.get("hardware_info", {}).get("cpu_model", "")
            )
        }

        if not trait_names:
            print("No CPU models found to create traits from.")
            return

        # Log generated trait names
        self.log("Generated trait names:")
        for trait_name in sorted(trait_names):
            self.log(f"  - {trait_name}")

        # Check OpenStack environment variables first
        self.check_openstack_environment()

        # Check OpenStack connectivity
        if not self._check_openstack_connectivity():
            print("Error: Cannot connect to OpenStack services", file=sys.stderr)
            sys.exit(1)

        # Note: We'll check trait existence in real-time during creation
        # This avoids issues with stale cached trait lists

        # Create traits in OpenStack
        created_count = 0
        already_existed_count = 0
        error_count = 0

        for trait_name in sorted(trait_names):
            self.log(f"Processing trait: '{trait_name}'")

            # Try to create the trait using the helper method
            try:
                success, status = self._create_trait(trait_name)

                if success:
                    if status == "created":
                        print(f"  ✓ {trait_name:<60} (Created)")
                        created_count += 1
                    elif status == "already_exists":
                        print(f"  ✓ {trait_name:<60} (Already exists)")
                        already_existed_count += 1
                else:
                    print(f"  ✗ {trait_name:<60} (Failed to create)")
                    error_count += 1

            except Exception as e:
                self.log(f"Error creating trait {trait_name}: {e}")
                print(f"  ✗ {trait_name:<60} (Failed to create)")
                error_count += 1

        print()
        print("Summary")

        # Build summary table with trait creation results
        summary_columns = ["Status", "Count"]
        summary_rows = []

        if created_count > 0:
            summary_rows.append(["Created", str(created_count)])
        if already_existed_count > 0:
            summary_rows.append(["Already exists", str(already_existed_count)])
        if error_count > 0:
            summary_rows.append(["Errors", str(error_count)])

        # Print summary table using PrettyTable
        self.print_table(summary_columns, summary_rows)

    def assign_cpu_traits_to_hypervisors(
        self, machines: List[Dict], zone: str, deployed_only: bool
    ) -> None:
        """Assign CPU traits to OpenStack hypervisors based on MAAS machine CPU models"""
        if not self.assign_traits_to_hypervisors:
            return

        print()
        self.log(
            "Assigning CPU traits to OpenStack hypervisors based on MAAS machine CPU models"
        )
        print("Assigning CPU Traits to Hypervisors")

        # Filter machines to get only deployed ones with Intel/AMD CPUs
        filtered_machines = self.filter_machines(
            machines, zone, deployed_only, self.tags
        )

        # Only process deployed machines for hypervisor mapping
        deployed_machines = []
        for machine in filtered_machines:
            if machine.get("status_name") == "Deployed":
                cpu_model = machine.get("hardware_info", {}).get("cpu_model", "")
                if self._INTEL_AMD_PATTERN.search(cpu_model):
                    deployed_machines.append(machine)

        if not deployed_machines:
            print("No deployed machines found with Intel or AMD CPUs.")
            return

        # Check OpenStack environment variables
        self.check_openstack_environment()

        # Check OpenStack connectivity
        if not self._check_openstack_connectivity():
            print("Error: Cannot connect to OpenStack services", file=sys.stderr)
            return

        # Get list of hypervisors from OpenStack
        try:
            self.log("Fetching OpenStack hypervisors...")
            hypervisors = self._get_hypervisors()
            self.log(f"Found {len(hypervisors)} hypervisors in OpenStack")
        except Exception as e:
            print(f"Error: Failed to fetch OpenStack hypervisors: {e}", file=sys.stderr)
            return

        # Create mapping of hostname to hypervisor
        hypervisor_map = {}
        for hv in hypervisors:
            # Try multiple attributes to get the hostname
            hv_hostname = (
                hv.get("hypervisor_hostname") or hv.get("name") or hv.get("hostname")
            )
            if hv_hostname:
                hypervisor_map[hv_hostname] = hv
                self.log(f"Mapped hypervisor: {hv_hostname}")
            else:
                self.log(f"Could not determine hostname for hypervisor: {hv}")

        self.log(f"Created hypervisor mapping for {len(hypervisor_map)} hypervisors")

        # Process each machine (traits should already exist from --create-openstack-traits phase)
        added_count = 0
        already_existed_count = 0
        not_found_count = 0
        error_count = 0

        for machine in deployed_machines:
            hostname = machine.get("hostname", "")
            cpu_model = machine.get("hardware_info", {}).get("cpu_model", "")
            trait_name = self.generate_trait_name(cpu_model)

            self.log(f"Processing machine: {hostname} with trait: {trait_name}")

            # Find corresponding hypervisor
            hypervisor = None
            for hv_hostname, hv in hypervisor_map.items():
                if hostname.lower() == hv_hostname.lower():
                    hypervisor = hv
                    break

            if not hypervisor:
                print(f"  ✗ {hostname:<60} (Hypervisor not found)")
                not_found_count += 1
                continue

            # Add trait to hypervisor
            try:
                # Get hypervisor hostname with fallback
                hv_hostname = (
                    hypervisor.get("hypervisor_hostname")
                    or hypervisor.get("name")
                    or hostname
                )

                self.log(f"Adding trait {trait_name} to hypervisor {hv_hostname}")

                # Get resource provider for the hypervisor
                # In OpenStack, hypervisors are represented as resource providers
                resource_providers = self._get_resource_providers()
                resource_provider = None

                # Try multiple matching strategies (ordered by preference)
                hv_hostname_lower = hv_hostname.lower()
                for rp in resource_providers:
                    rp_name = rp.get("name", "")
                    rp_name_lower = rp_name.lower()
                    # Exact match (highest priority)
                    if rp_name == hv_hostname:
                        resource_provider = rp
                        break
                    # Case-insensitive exact match
                    elif rp_name_lower == hv_hostname_lower:
                        resource_provider = rp
                        break
                    # Hypervisor hostname contained in resource provider name
                    elif hv_hostname_lower in rp_name_lower:
                        resource_provider = rp
                        break
                    # Resource provider name contained in hypervisor hostname
                    elif rp_name_lower in hv_hostname_lower:
                        resource_provider = rp
                        break

                if not resource_provider:
                    # Log available resource providers for debugging
                    rp_names = [rp.get("name", "") for rp in resource_providers]
                    self.log(f"Available resource providers: {rp_names}")
                    self.log(f"Looking for hypervisor: {hv_hostname}")
                    print(f"  ✗ {hostname:<60} (Resource provider not found)")
                    error_count += 1
                    continue

                # Add trait to resource provider using HTTP API
                trait_was_added = False
                try:
                    # Trait should already exist from the upfront creation phase

                    # Get current traits for the resource provider using helper method
                    current_trait_names = self._get_resource_provider_traits(
                        resource_provider["uuid"]
                    )

                    # Filter to show only CUSTOM traits for cleaner logging
                    custom_traits = [
                        trait
                        for trait in current_trait_names
                        if self._CUSTOM_TRAIT_PATTERN.match(trait)
                    ]
                    self.log(
                        f"Current CUSTOM traits for {resource_provider['uuid']}: {custom_traits}"
                    )
                    if len(current_trait_names) > len(custom_traits):
                        self.log(
                            f"Total traits for {resource_provider['uuid']}: {len(current_trait_names)} (showing {len(custom_traits)} CUSTOM traits)"
                        )

                    # Check if the trait was already in the list
                    if trait_name in current_trait_names:
                        self.log(
                            f"Trait {trait_name} already exists on resource provider {resource_provider['uuid']}"
                        )
                        trait_was_added = False
                    else:
                        # Prepare the request with all traits (existing + new)
                        new_trait_names = current_trait_names + [trait_name]

                        # Use the helper method to set traits
                        success = self._set_resource_provider_traits(
                            resource_provider["uuid"], new_trait_names
                        )

                        if success:
                            self.log(
                                f"Successfully added trait {trait_name} to resource provider {resource_provider['uuid']}"
                            )
                            trait_was_added = True
                        else:
                            raise Exception(
                                f"Failed to set traits for resource provider {resource_provider['uuid']}"
                            )
                except Exception as http_error:
                    self.log(f"HTTP API approach failed: {http_error}")
                    raise http_error

                # Print appropriate status message
                if trait_was_added:
                    print(f"  ✓ {hostname:<60} (Trait added to hypervisor)")
                    added_count += 1
                else:
                    print(f"  ✓ {hostname:<60} (Trait already exists on hypervisor)")
                    already_existed_count += 1

            except Exception as e:
                self.log(f"Error adding trait to hypervisor {hostname}: {e}")
                print(f"  ✗ {hostname:<60} (Failed to add trait)")
                error_count += 1

        # Print summary
        print()
        print("Summary")

        summary_columns = ["Status", "Count"]
        summary_rows = [
            ["Added to hypervisors", str(added_count)],
            ["Already exists on hypervisors", str(already_existed_count)],
            ["Hypervisor not found", str(not_found_count)],
        ]
        if error_count > 0:
            summary_rows.append(["Errors", str(error_count)])

        self.print_table(summary_columns, summary_rows)

    def clear_openstack_traits(self) -> None:
        """Clear all CUSTOM traits from OpenStack hypervisors and delete the traits"""
        print()
        self.log(
            "Clearing all CUSTOM traits from OpenStack hypervisors and deleting traits"
        )
        print("Clearing OpenStack Traits")

        # Check OpenStack environment variables
        self.check_openstack_environment()

        # Check OpenStack connectivity
        if not self._check_openstack_connectivity():
            print("Error: Cannot connect to OpenStack services", file=sys.stderr)
            return

        # Get all resource providers (hypervisors)
        try:
            self.log("Fetching OpenStack resource providers...")
            resource_providers = self._get_resource_providers()
            self.log(f"Found {len(resource_providers)} resource providers")
        except Exception as e:
            print(
                f"Error: Failed to fetch OpenStack resource providers: {e}",
                file=sys.stderr,
            )
            return

        # Get all traits to find CUSTOM ones
        try:
            self.log("Fetching all traits...")
            all_traits_response = self._make_placement_api_request("GET", "/traits")
            if all_traits_response.status_code not in self.SUCCESS_HTTP_CODES:
                print(
                    f"Error: Failed to fetch traits: {all_traits_response.status_code} - {all_traits_response.text}",
                    file=sys.stderr,
                )
                return

            all_traits = all_traits_response.json().get("traits", [])
            custom_traits = [
                trait for trait in all_traits if self._CUSTOM_TRAIT_PATTERN.match(trait)
            ]
            self.log(f"Found {len(custom_traits)} CUSTOM traits to delete")
        except Exception as e:
            print(f"Error: Failed to fetch traits: {e}", file=sys.stderr)
            return

        # Clear traits from resource providers
        cleared_count = 0
        error_count = 0

        for resource_provider in resource_providers:
            rp_name = resource_provider.get("name", "")
            rp_uuid = resource_provider.get("uuid", "")

            if not rp_name or not rp_uuid:
                self.log(
                    f"Skipping resource provider with missing name or uuid: {resource_provider}"
                )
                continue

            self.log(f"Processing resource provider: {rp_name} ({rp_uuid})")

            # Get current traits for this resource provider
            try:
                current_traits = self._get_resource_provider_traits(rp_uuid)
                custom_traits_on_rp = [
                    trait
                    for trait in current_traits
                    if self._CUSTOM_TRAIT_PATTERN.match(trait)
                ]

                if not custom_traits_on_rp:
                    self.log(f"No CUSTOM traits found on {rp_name}")
                    continue

                self.log(
                    f"Found {len(custom_traits_on_rp)} CUSTOM traits on {rp_name}: {custom_traits_on_rp}"
                )

                # Remove CUSTOM traits from resource provider
                non_custom_traits = [
                    trait
                    for trait in current_traits
                    if not self._CUSTOM_TRAIT_PATTERN.match(trait)
                ]

                # Set traits to only non-CUSTOM traits (effectively removing CUSTOM ones)
                success = self._set_resource_provider_traits(rp_uuid, non_custom_traits)

                if success:
                    print(
                        f"  ✓ {rp_name:<60} (Cleared {len(custom_traits_on_rp)} CUSTOM traits)"
                    )
                    cleared_count += 1
                else:
                    print(f"  ✗ {rp_name:<60} (Failed to clear traits)")
                    error_count += 1

            except Exception as e:
                self.log(f"Error processing resource provider {rp_name}: {e}")
                print(f"  ✗ {rp_name:<60} (Error: {e})")
                error_count += 1

        print()

        # Delete CUSTOM traits from the placement service
        deleted_count = 0
        delete_error_count = 0

        self.log(
            f"Deleting {len(custom_traits)} CUSTOM traits from placement service..."
        )
        for trait_name in sorted(custom_traits):
            try:
                # Delete the trait
                response = self._make_placement_api_request(
                    "DELETE", f"/traits/{trait_name}"
                )

                if response.status_code in self.SUCCESS_HTTP_CODES:
                    print(f"  ✓ {trait_name:<60} (Deleted)")
                    deleted_count += 1
                else:
                    print(
                        f"  ✗ {trait_name:<60} (Failed to delete: {response.status_code})"
                    )
                    delete_error_count += 1

            except Exception as e:
                self.log(f"Error deleting trait {trait_name}: {e}")
                print(f"  ✗ {trait_name:<60} (Error: {e})")
                delete_error_count += 1

        print()
        print("Summary")

        # Build summary table
        summary_columns = ["Operation", "Status", "Count"]
        summary_rows = []

        if cleared_count > 0:
            summary_rows.append(["Clear from RPs", "Success", str(cleared_count)])
        if error_count > 0:
            summary_rows.append(["Clear from RPs", "Errors", str(error_count)])
        if deleted_count > 0:
            summary_rows.append(["Delete traits", "Success", str(deleted_count)])
        if delete_error_count > 0:
            summary_rows.append(["Delete traits", "Errors", str(delete_error_count)])

        self.print_table(summary_columns, summary_rows)

    def run(
        self,
        zone: str,
        deployed_only: bool,
        tags: List[str],
        create_openstack_traits: bool,
        assign_traits_to_hypervisors: bool = False,
        clear_openstack_traits: bool = False,
    ) -> None:
        """Main execution method"""
        self.tags = tags
        self.should_create_openstack_traits = create_openstack_traits
        self.assign_traits_to_hypervisors = assign_traits_to_hypervisors

        if clear_openstack_traits:
            # Clear traits mode - no need for MAAS data
            self.clear_openstack_traits()
            return

        self.check_dependencies()
        machines = self.fetch_maas_data()
        self.print_machine_table(machines, zone, deployed_only)
        self.print_cpu_distribution(machines, zone, deployed_only)
        self.create_openstack_traits(machines, zone, deployed_only)

        if self.assign_traits_to_hypervisors:
            self.assign_cpu_traits_to_hypervisors(machines, zone, deployed_only)

        self.log("Script completed successfully")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="MAAS CPU Analyzer - Analyze CPU models in MAAS machines and optionally create OpenStack traits for resource scheduling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables Required:
  MAAS_URL        - MAAS server URL (e.g., http://maas.example.com:5240/MAAS)
  MAAS_API_KEY    - MAAS API key for authentication

  For OpenStack operations (--create-openstack-traits, --clear-openstack-traits), also set:
  OS_AUTH_URL     - OpenStack authentication URL
  OS_USERNAME     - OpenStack username
  OS_PASSWORD     - OpenStack password
  OS_PROJECT_NAME - OpenStack project name

Examples:
  %(prog)s                                  # Show all machines in all zones
  %(prog)s --zone zone-1                    # Show all machines in zone-1
  %(prog)s --zone zone-1 --deployed-only    # Show only deployed machines in zone-1
  %(prog)s --zone zone-1 --tags compute,gpu # Show all machines with 'compute' or 'gpu' tags in zone-1
  %(prog)s --zone zone-1 --deployed-only --tags compute # Show deployed machines with 'compute' tag in zone-1
  %(prog)s --zone zone-1 --create-openstack-traits # Create OpenStack traits for zone-1
  %(prog)s --zone zone-1 --create-openstack-traits --assign-traits-to-hypervisors # Create OpenStack traits and assign them to hypervisors
  %(prog)s --zone zone-1 --clear-openstack-traits # Clear OpenStack traits for zone-1
  %(prog)s --zone zone-1 --verbose # Create traits with debug info
        """,
    )

    parser.add_argument(
        "--zone",
        help="MAAS zone name to filter machines (optional, shows all zones by default)",
    )
    parser.add_argument(
        "--deployed-only",
        action="store_true",
        help="Only show deployed machines",
    )
    parser.add_argument(
        "--all-machines",
        action="store_true",
        default=True,
        help="Show all machines regardless of status (default)",
    )
    parser.add_argument("--tags", help="Filter by MAAS tags (comma-separated)")
    parser.add_argument(
        "--create-openstack-traits",
        action="store_true",
        help="Create OpenStack traits from CPU models",
    )
    parser.add_argument(
        "--assign-traits-to-hypervisors",
        action="store_true",
        help="Assign CPU traits to OpenStack hypervisors based on MAAS machine CPU models (requires --create-openstack-traits)",
    )
    parser.add_argument(
        "--clear-openstack-traits",
        action="store_true",
        help="Clear all CUSTOM traits from OpenStack hypervisors and delete the traits",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output for debugging",
    )

    args = parser.parse_args()

    # Validate that --assign-traits-to-hypervisors requires --create-openstack-traits
    if args.assign_traits_to_hypervisors and not args.create_openstack_traits:
        print(
            "Error: --assign-traits-to-hypervisors requires --create-openstack-traits to be specified",
            file=sys.stderr,
        )
        print(
            "Usage: --create-openstack-traits --assign-traits-to-hypervisors",
            file=sys.stderr,
        )
        sys.exit(1)

    # Validate that --clear-openstack-traits is not used with conflicting flags
    if args.clear_openstack_traits and (
        args.create_openstack_traits or args.assign_traits_to_hypervisors
    ):
        print(
            "Error: --clear-openstack-traits cannot be used with --create-openstack-traits or --assign-traits-to-hypervisors",
            file=sys.stderr,
        )
        print(
            "Usage: --clear-openstack-traits (standalone)",
            file=sys.stderr,
        )
        sys.exit(1)

    deployed_only = args.deployed_only
    tags = (
        [tag.strip() for tag in args.tags.split(",") if tag.strip()]
        if args.tags
        else []
    )

    analyzer = MAASCPUAnalyzer(verbose=args.verbose)
    analyzer.run(
        args.zone,
        deployed_only,
        tags,
        args.create_openstack_traits,
        args.assign_traits_to_hypervisors,
        args.clear_openstack_traits,
    )


if __name__ == "__main__":
    main()
