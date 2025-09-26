"""
MAAS client module for MAAS CPU Analyzer.

This module handles all MAAS-related operations including:
- API authentication
- Machine data fetching
- Data filtering and processing
"""

import json
import os
import sys
from typing import Dict, List, Optional

import requests
from requests_oauthlib import OAuth1

from .utils import MachineFilterUtils


class MAASClient:
    """MAAS client for handling MAAS API operations"""

    def __init__(self, verbose: bool = False):
        """Initialize MAAS client"""
        self.verbose = verbose
        self._session = None

    def log(self, message: str) -> None:
        """Log message if verbose mode is enabled"""
        if self.verbose:
            print(f"[MAAS] {message}")

    def _get_session(self):
        """Get or create HTTP session"""
        if self._session is None:
            self._session = requests.Session()
        return self._session

    def _clear_cache(self) -> None:
        """Clear cached session"""
        self._session = None

    def fetch_maas_data(self) -> List[Dict]:
        """Fetch machine data from MAAS API"""
        self.log("Fetching machine data from MAAS...")

        # Get MAAS configuration from environment
        maas_url, maas_api_key = self._get_maas_config()

        # Parse and validate API key
        consumer_key, token_key, token_secret = self._parse_maas_api_key(maas_api_key)

        # Configure OAuth authentication
        auth = self._configure_maas_oauth(consumer_key, token_key, token_secret)

        # Make API request
        return self._make_maas_api_request(maas_url, auth)

    def _get_maas_config(self) -> tuple:
        """Get MAAS configuration from environment"""
        maas_url = os.environ.get("MAAS_URL")
        maas_api_key = os.environ.get("MAAS_API_KEY")

        if not maas_url or not maas_api_key:
            print(
                "Error: MAAS_URL and MAAS_API_KEY environment variables must be set",
                file=sys.stderr,
            )
            sys.exit(1)

        return maas_url, maas_api_key

    def _parse_maas_api_key(self, maas_api_key: str) -> tuple:
        """Parse and validate MAAS API key"""
        api_key_parts = maas_api_key.split(":")
        if len(api_key_parts) != 3:
            print(
                "Error: MAAS_API_KEY must be in format 'consumer_key:token_key:token_secret'",
                file=sys.stderr,
            )
            sys.exit(1)

        return api_key_parts[0], api_key_parts[1], api_key_parts[2]

    def _configure_maas_oauth(
        self, consumer_key: str, token_key: str, token_secret: str
    ) -> OAuth1:
        """Configure OAuth 1.0a for MAAS API authentication"""
        return OAuth1(
            consumer_key,
            client_secret="",  # MAAS doesn't use client secret
            resource_owner_key=token_key,
            resource_owner_secret=token_secret,
            signature_method="PLAINTEXT",
            signature_type="AUTH_HEADER",
        )

    def _make_maas_api_request(self, maas_url: str, auth: OAuth1) -> List[Dict]:
        """Make API request to MAAS"""
        api_url = f"{maas_url.rstrip('/')}/api/2.0/machines/"

        try:
            return self._execute_maas_request(api_url, auth)
        except requests.exceptions.RequestException as e:
            self._handle_maas_request_error(e)
            return []  # This line will never be reached due to sys.exit(1) in handler
        except json.JSONDecodeError as e:
            print(f"Error: Failed to parse MAAS JSON data: {e}", file=sys.stderr)
            sys.exit(1)

    def _execute_maas_request(self, api_url: str, auth: OAuth1) -> List[Dict]:
        """Execute the MAAS API request"""
        self.log(f"Making request to: {api_url}")
        session = self._get_session()
        response = session.get(api_url, auth=auth, timeout=30)

        self.log(f"Response status: {response.status_code}")
        self.log(f"Response headers: {dict(response.headers)}")
        if response.status_code != 200:
            self.log(f"Response body: {response.text}")

        response.raise_for_status()

        self.log("Successfully fetched machine data")
        return response.json()

    def _handle_maas_request_error(
        self, e: requests.exceptions.RequestException
    ) -> None:
        """Handle MAAS request errors"""
        print(f"Error: Failed to fetch MAAS data: {e}", file=sys.stderr)
        if hasattr(e, "response") and e.response is not None and self.verbose:
            print(f"Response status: {e.response.status_code}", file=sys.stderr)
            print(f"Response body: {e.response.text}", file=sys.stderr)
        sys.exit(1)

    def filter_machines(
        self,
        machines: List[Dict],
        zone: Optional[str],
        deployed_only: bool,
        tags: List[str],
    ) -> List[Dict]:
        """Filter machines based on zone, deployment status, and tags"""
        return MachineFilterUtils.filter_machines(
            machines, zone or "", deployed_only, tags
        )
