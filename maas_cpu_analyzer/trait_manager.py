"""
Trait management module for MAAS CPU Analyzer.

This module handles all trait-related operations including:
- Trait creation and management
- Trait assignment to hypervisors
- Trait clearing operations
"""

import sys
from typing import Dict, List, Optional

from .utils import CPUUtils, MachineFilterUtils, TableUtils


class TraitManager:
    """Manages trait operations for the MAAS CPU Analyzer"""

    def __init__(self, openstack_client, verbose: bool = False, analyzer=None):
        """Initialize trait manager"""
        self.openstack_client = openstack_client
        self.verbose = verbose
        # Optional back-reference to main analyzer for test patchability
        self._analyzer = analyzer

    def log(self, message: str) -> None:
        """Log message if verbose mode is enabled"""
        if self.verbose:
            print(f"[TraitManager] {message}")

    def create_traits_from_machines(
        self, machines: List[Dict], zone: str, deployed_only: bool, tags: List[str]
    ) -> None:
        """Create OpenStack traits from CPU models in machines"""
        print()
        self.log("Generating and creating OpenStack trait names")
        print("Creating OpenStack Traits")

        # Get unique CPU models and generate trait names
        trait_names = self._generate_trait_names_from_machines(
            machines, zone, deployed_only, tags
        )
        if not trait_names:
            return

        # Log generated trait names
        self._log_generated_trait_names(trait_names)

        # Validate OpenStack connectivity
        if not self._validate_openstack_for_trait_creation():
            return

        # Create traits in OpenStack
        results = self._create_traits_in_openstack(trait_names)

        # Print summary
        self._print_trait_creation_summary(results)

    def _generate_trait_names_from_machines(
        self, machines: List[Dict], zone: str, deployed_only: bool, tags: List[str]
    ) -> set:
        """Generate trait names from filtered machines"""
        filtered_machines = self._filter_machines_for_traits(
            machines, zone, deployed_only, tags
        )

        trait_names = {
            CPUUtils.generate_trait_name(
                machine.get("hardware_info", {}).get("cpu_model", "")
            )
            for machine in filtered_machines
            if CPUUtils.is_intel_amd_cpu(
                machine.get("hardware_info", {}).get("cpu_model", "")
            )
        }

        if not trait_names:
            print("No CPU models found to create traits from.")
            return set()

        return trait_names

    def _filter_machines_for_traits(
        self, machines: List[Dict], zone: str, deployed_only: bool, tags: List[str]
    ) -> List[Dict]:
        """Filter machines for trait creation"""
        return MachineFilterUtils.filter_machines(machines, zone, deployed_only, tags)

    def _log_generated_trait_names(self, trait_names: set) -> None:
        """Log generated trait names"""
        self.log("Generated trait names:")
        for trait_name in sorted(trait_names):
            self.log(f"  - {trait_name}")

    def _validate_openstack_for_trait_creation(self) -> bool:
        """Validate OpenStack environment and connectivity for trait creation"""
        self.openstack_client.check_openstack_environment()

        # Prefer analyzer wrapper if available (enables easier test patching)
        if self._analyzer is not None:
            # pylint: disable=protected-access
            is_connected = self._analyzer._check_openstack_connectivity()
        else:
            is_connected = self.openstack_client.check_openstack_connectivity()

        if not is_connected:
            print("Error: Cannot connect to OpenStack services", file=sys.stderr)
            sys.exit(1)

        return True

    def _create_traits_in_openstack(self, trait_names: set) -> Dict[str, int]:
        """Create traits in OpenStack and return results"""
        created_count = 0
        already_existed_count = 0
        error_count = 0

        for trait_name in sorted(trait_names):
            result = self._process_single_trait_creation(trait_name)
            if result == "created":
                created_count += 1
            elif result == "already_exists":
                already_existed_count += 1
            elif result == "error":
                error_count += 1

        return {
            "created_count": created_count,
            "already_existed_count": already_existed_count,
            "error_count": error_count,
        }

    def _process_single_trait_creation(self, trait_name: str) -> str:
        """Process creation of a single trait"""
        self.log(f"Processing trait: '{trait_name}'")

        try:
            success, status = self.openstack_client.create_trait(trait_name)

            if success:
                if status == "created":
                    print(f"  ✓ {trait_name:<60} (Created)")
                    return "created"
                if status == "already_exists":
                    print(f"  ✓ {trait_name:<60} (Already exists)")
                    return "already_exists"
            print(f"  ✗ {trait_name:<60} (Failed to create)")
            return "error"

        except Exception as e:
            self.log(f"Error creating trait {trait_name}: {e}")
            print(f"  ✗ {trait_name:<60} (Failed to create)")
            return "error"

    def _print_trait_creation_summary(self, results: Dict[str, int]) -> None:
        """Print summary of trait creation results"""
        print()
        print("Summary")

        summary_columns = ["Status", "Count"]
        summary_rows = []

        if results["created_count"] > 0:
            summary_rows.append(["Created", str(results["created_count"])])
        if results["already_existed_count"] > 0:
            summary_rows.append(
                ["Already exists", str(results["already_existed_count"])]
            )
        if results["error_count"] > 0:
            summary_rows.append(["Errors", str(results["error_count"])])

        TableUtils.print_table(summary_columns, summary_rows)

    def assign_traits_to_hypervisors(
        self, machines: List[Dict], zone: str, deployed_only: bool, tags: List[str]
    ) -> None:
        """Assign CPU traits to OpenStack hypervisors based on MAAS machine CPU models"""
        print()
        self.log("Assigning CPU traits to OpenStack hypervisors")
        print("Assigning Traits to Hypervisors")

        # Validate OpenStack connectivity
        if not self._validate_openstack_connectivity():
            return

        # Get deployed machines with Intel/AMD CPUs
        deployed_machines = self._get_deployed_machines(machines, zone, tags)
        if not deployed_machines:
            print("No deployed machines with Intel or AMD CPUs found.")
            return

        # Create hypervisor mapping
        hypervisor_map = self._create_hypervisor_mapping()
        if not hypervisor_map:
            print("No hypervisors found in OpenStack.")
            return

        # Process each machine and assign traits to hypervisors
        results = self._process_machines_for_traits(deployed_machines, hypervisor_map)

        # Print summary
        self._print_trait_assignment_summary(results)

    def _validate_openstack_connectivity(self) -> bool:
        """Validate OpenStack connectivity"""
        self.openstack_client.check_openstack_environment()

        if not self.openstack_client.check_openstack_connectivity():
            print("Error: Cannot connect to OpenStack services", file=sys.stderr)
            return False

        return True

    def _get_deployed_machines(
        self, machines: List[Dict], zone: str, tags: List[str]
    ) -> List[Dict]:
        """Get deployed machines with Intel/AMD CPUs"""
        deployed_machines = self._filter_machines_for_traits(
            machines, zone, True, tags  # deployed_only=True
        )

        # Filter for Intel/AMD CPUs only
        cpu_machines = []
        for machine in deployed_machines:
            cpu_model = machine.get("hardware_info", {}).get("cpu_model", "")
            if CPUUtils.is_intel_amd_cpu(cpu_model):
                cpu_machines.append(machine)

        return cpu_machines

    def _create_hypervisor_mapping(self) -> Dict[str, Dict]:
        """Create mapping of hostname to hypervisor"""
        hypervisors = self._fetch_hypervisors_for_mapping()
        if not hypervisors:
            return {}

        return self._build_hypervisor_mapping(hypervisors)

    def _fetch_hypervisors_for_mapping(self) -> List[Dict]:
        """Fetch hypervisors for mapping"""
        try:
            self.log("Fetching OpenStack hypervisors...")
            hypervisors = self.openstack_client.get_hypervisors()
            self.log(f"Found {len(hypervisors)} hypervisors in OpenStack")
            return hypervisors
        except Exception as e:
            print(f"Error: Failed to fetch OpenStack hypervisors: {e}", file=sys.stderr)
            return []

    def _build_hypervisor_mapping(self, hypervisors: List[Dict]) -> Dict[str, Dict]:
        """Build hypervisor mapping from list"""
        hypervisor_map = {}
        for hv in hypervisors:
            hv_hostname = self._extract_hypervisor_hostname(hv)
            if hv_hostname:
                hypervisor_map[hv_hostname] = hv
                self.log(f"Mapped hypervisor: {hv_hostname}")
            else:
                self.log(f"Could not determine hostname for hypervisor: {hv}")

        self.log(f"Created hypervisor mapping for {len(hypervisor_map)} hypervisors")
        return hypervisor_map

    def _extract_hypervisor_hostname(self, hv: Dict) -> Optional[str]:
        """Extract hostname from hypervisor"""
        return hv.get("hypervisor_hostname") or hv.get("name") or hv.get("hostname")

    def _process_machines_for_traits(
        self, deployed_machines: List[Dict], hypervisor_map: Dict[str, Dict]
    ) -> Dict[str, int]:
        """Process each machine and assign traits to hypervisors"""
        results = {
            "added_count": 0,
            "already_existed_count": 0,
            "not_found_count": 0,
            "error_count": 0,
        }

        for machine in deployed_machines:
            result = self._process_single_machine_for_traits(machine, hypervisor_map)
            results[result] += 1

        return results

    def _process_single_machine_for_traits(
        self, machine: Dict, hypervisor_map: Dict[str, Dict]
    ) -> str:
        """Process a single machine for trait assignment"""
        hostname = machine.get("hostname", "")
        cpu_model = machine.get("hardware_info", {}).get("cpu_model", "")
        trait_name = CPUUtils.generate_trait_name(cpu_model)

        # Find hypervisor for this machine
        hypervisor = self._find_hypervisor_for_machine(hostname, hypervisor_map)
        if not hypervisor:
            print(f"  ✗ {hostname:<60} (Hypervisor not found)")
            return "not_found_count"

        # Assign trait to hypervisor
        return self._assign_trait_to_hypervisor(machine, hypervisor, trait_name)

    def _find_hypervisor_for_machine(
        self, hostname: str, hypervisor_map: Dict[str, Dict]
    ) -> Optional[Dict]:
        """Find hypervisor for a machine hostname"""
        # Try exact match first
        if hostname in hypervisor_map:
            return hypervisor_map[hostname]

        # Try case-insensitive match
        hypervisor = self._find_case_insensitive_match(hostname, hypervisor_map)
        if hypervisor:
            return hypervisor

        # Try partial match
        return self._find_partial_match(hostname, hypervisor_map)

    def _find_case_insensitive_match(
        self, hostname: str, hypervisor_map: Dict[str, Dict]
    ) -> Optional[Dict]:
        """Find hypervisor using case-insensitive match"""
        hostname_lower = hostname.lower()
        for hv_hostname, hypervisor in hypervisor_map.items():
            if hv_hostname.lower() == hostname_lower:
                return hypervisor
        return None

    def _find_partial_match(
        self, hostname: str, hypervisor_map: Dict[str, Dict]
    ) -> Optional[Dict]:
        """Find hypervisor using partial match"""
        hostname_lower = hostname.lower()
        for hv_hostname, hypervisor in hypervisor_map.items():
            if (
                hostname_lower in hv_hostname.lower()
                or hv_hostname.lower() in hostname_lower
            ):
                return hypervisor
        return None

    def _assign_trait_to_hypervisor(
        self, machine: Dict, hypervisor: Dict, trait_name: str
    ) -> str:
        """Assign trait to hypervisor and return result type"""
        hostname = machine.get("hostname", "")

        try:
            return self._process_trait_assignment(
                machine, hypervisor, trait_name, hostname
            )
        except Exception as e:
            return self._handle_trait_assignment_error(hostname, e)

    def _process_trait_assignment(
        self, machine: Dict, hypervisor: Dict, trait_name: str, hostname: str
    ) -> str:
        """Process the trait assignment logic"""
        hv_hostname = self._get_hypervisor_hostname(hypervisor, hostname)
        self.log(f"Adding trait {trait_name} to hypervisor {hv_hostname}")

        resource_provider = self._find_resource_provider_for_hypervisor(hv_hostname)
        if not resource_provider:
            return self._handle_resource_provider_not_found(hostname)

        trait_was_added = self._add_trait_to_resource_provider(
            resource_provider, trait_name
        )
        return self._handle_trait_assignment_result(hostname, trait_was_added)

    def _get_hypervisor_hostname(self, hypervisor: Dict, fallback_hostname: str) -> str:
        """Get hypervisor hostname with fallback"""
        return (
            hypervisor.get("hypervisor_hostname")
            or hypervisor.get("name")
            or fallback_hostname
        )

    def _handle_resource_provider_not_found(self, hostname: str) -> str:
        """Handle case when resource provider is not found"""
        print(f"  ✗ {hostname:<60} (Resource provider not found)")
        return "error_count"

    def _handle_trait_assignment_result(
        self, hostname: str, trait_was_added: bool
    ) -> str:
        """Handle the result of trait assignment"""
        if trait_was_added:
            print(f"  ✓ {hostname:<60} (Trait added to hypervisor)")
            return "added_count"
        print(f"  ✓ {hostname:<60} (Trait already exists on hypervisor)")
        return "already_existed_count"

    def _handle_trait_assignment_error(self, hostname: str, error: Exception) -> str:
        """Handle errors during trait assignment"""
        self.log(f"Error adding trait to hypervisor {hostname}: {error}")
        print(f"  ✗ {hostname:<60} (Failed to add trait)")
        return "error_count"

    def _find_resource_provider_for_hypervisor(
        self, hv_hostname: str
    ) -> Optional[Dict]:
        """Find resource provider for a hypervisor using multiple matching strategies"""
        resource_providers = self.openstack_client.get_resource_providers()
        hv_hostname_lower = hv_hostname.lower()

        for rp in resource_providers:
            if self._is_resource_provider_match(rp, hv_hostname, hv_hostname_lower):
                return rp

        # Log available resource providers for debugging
        self._log_resource_provider_debug_info(resource_providers, hv_hostname)
        return None

    def _is_resource_provider_match(
        self, rp: Dict, hv_hostname: str, hv_hostname_lower: str
    ) -> bool:
        """Check if resource provider matches hypervisor hostname"""
        rp_name = rp.get("name", "")
        rp_name_lower = rp_name.lower()

        # Try multiple matching strategies (ordered by preference)
        return (
            rp_name == hv_hostname
            or rp_name_lower == hv_hostname_lower
            or hv_hostname_lower in rp_name_lower
            or rp_name_lower in hv_hostname_lower
        )

    def _log_resource_provider_debug_info(
        self, resource_providers: List[Dict], hv_hostname: str
    ) -> None:
        """Log debug information for resource provider lookup"""
        rp_names = [rp.get("name", "") for rp in resource_providers]
        self.log(f"Available resource providers: {rp_names}")
        self.log(f"Looking for hypervisor: {hv_hostname}")

    def _add_trait_to_resource_provider(
        self, resource_provider: Dict, trait_name: str
    ) -> bool:
        """Add trait to resource provider and return whether it was added"""
        try:
            # Get current traits for the resource provider
            current_trait_names = self.openstack_client.get_resource_provider_traits(
                resource_provider["uuid"]
            )

            # Log current traits
            self._log_current_traits(resource_provider["uuid"], current_trait_names)

            # Check if trait already exists
            if trait_name in current_trait_names:
                self.log(
                    f"Trait {trait_name} already exists on resource provider {resource_provider['uuid']}"
                )
                return False

            # Add the new trait
            return self._add_new_trait_to_provider(
                resource_provider["uuid"], current_trait_names, trait_name
            )

        except Exception as http_error:
            self.log(f"HTTP API approach failed: {http_error}")
            raise http_error

    def _log_current_traits(self, rp_uuid: str, current_trait_names: List[str]) -> None:
        """Log current traits for resource provider"""
        # Log current CUSTOM traits for cleaner output
        custom_traits = [
            trait for trait in current_trait_names if CPUUtils.is_custom_trait(trait)
        ]
        self.log(f"Current CUSTOM traits for {rp_uuid}: {custom_traits}")
        if len(current_trait_names) > len(custom_traits):
            self.log(
                f"Total traits for {rp_uuid}: {len(current_trait_names)} (showing {len(custom_traits)} CUSTOM traits)"
            )

    def _add_new_trait_to_provider(
        self, rp_uuid: str, current_trait_names: List[str], trait_name: str
    ) -> bool:
        """Add new trait to resource provider"""
        new_trait_names = current_trait_names + [trait_name]
        success = self.openstack_client.set_resource_provider_traits(
            rp_uuid, new_trait_names
        )

        if success:
            self.log(
                f"Successfully added trait {trait_name} to resource provider {rp_uuid}"
            )
            return True
        raise Exception(f"Failed to set traits for resource provider {rp_uuid}")

    def _print_trait_assignment_summary(self, results: Dict[str, int]) -> None:
        """Print summary of trait assignment results"""
        print()
        print("Summary")

        summary_columns = ["Status", "Count"]
        summary_rows = [
            ["Added to hypervisors", str(results["added_count"])],
            ["Already exists on hypervisors", str(results["already_existed_count"])],
            ["Hypervisor not found", str(results["not_found_count"])],
        ]
        if results["error_count"] > 0:
            summary_rows.append(["Errors", str(results["error_count"])])

        TableUtils.print_table(summary_columns, summary_rows)

    def clear_openstack_traits(self) -> None:
        """Clear all CUSTOM traits from OpenStack hypervisors and delete the traits"""
        print()
        self.log(
            "Clearing all CUSTOM traits from OpenStack hypervisors and deleting traits"
        )
        print("Clearing OpenStack Traits")

        if not self._validate_openstack_for_clearing():
            return

        resource_providers = self._get_resource_providers_for_clearing()
        if not resource_providers:
            return

        custom_traits = self._get_custom_traits_for_clearing()
        if custom_traits is None:
            return

        # Clear traits from resource providers
        clear_results = self._clear_traits_from_resource_providers(resource_providers)

        # Delete CUSTOM traits from the placement service
        delete_results = self._delete_custom_traits_from_placement(custom_traits)

        # Print summary
        self._print_clearing_summary(clear_results, delete_results)

    def _validate_openstack_for_clearing(self) -> bool:
        """Validate OpenStack environment and connectivity for clearing traits"""
        self.openstack_client.check_openstack_environment()

        if not self.openstack_client.check_openstack_connectivity():
            print("Error: Cannot connect to OpenStack services", file=sys.stderr)
            return False

        return True

    def _get_resource_providers_for_clearing(self) -> List[Dict]:
        """Get resource providers for clearing traits"""
        try:
            self.log("Fetching OpenStack resource providers...")
            resource_providers = self.openstack_client.get_resource_providers()
            self.log(f"Found {len(resource_providers)} resource providers")
            return resource_providers
        except Exception as e:
            print(
                f"Error: Failed to fetch OpenStack resource providers: {e}",
                file=sys.stderr,
            )
            return []

    def _get_custom_traits_for_clearing(self) -> Optional[List[str]]:
        """Get CUSTOM traits for clearing"""
        try:
            self.log("Fetching all traits...")
            all_traits_response = self.openstack_client.make_placement_api_request(
                "GET", "/traits"
            )
            if (
                all_traits_response.status_code
                not in self.openstack_client.SUCCESS_HTTP_CODES
            ):
                print(
                    f"Error: Failed to fetch traits: {all_traits_response.status_code} - {all_traits_response.text}",
                    file=sys.stderr,
                )
                return None

            all_traits = all_traits_response.json().get("traits", [])
            custom_traits = [
                trait for trait in all_traits if CPUUtils.is_custom_trait(trait)
            ]
            self.log(f"Found {len(custom_traits)} CUSTOM traits to delete")
            return custom_traits
        except Exception as e:
            print(f"Error: Failed to fetch traits: {e}", file=sys.stderr)
            return None

    def _clear_traits_from_resource_providers(
        self, resource_providers: List[Dict]
    ) -> Dict[str, int]:
        """Clear traits from resource providers and return results"""
        cleared_count = 0
        error_count = 0

        for resource_provider in resource_providers:
            result = self._clear_traits_from_single_provider(resource_provider)
            if result == "success":
                cleared_count += 1
            elif result == "error":
                error_count += 1

        return {"cleared_count": cleared_count, "error_count": error_count}

    def _clear_traits_from_single_provider(self, resource_provider: Dict) -> str:
        """Clear traits from a single resource provider"""
        rp_name = resource_provider.get("name", "")
        rp_uuid = resource_provider.get("uuid", "")

        if not rp_name or not rp_uuid:
            self.log(
                f"Skipping resource provider with missing name or uuid: {resource_provider}"
            )
            return "skip"

        self.log(f"Processing resource provider: {rp_name} ({rp_uuid})")

        try:
            return self._process_provider_traits_clearing(rp_name, rp_uuid)
        except Exception as e:
            self.log(f"Error processing resource provider {rp_name}: {e}")
            print(f"  ✗ {rp_name:<60} (Error: {e})")
            return "error"

    def _process_provider_traits_clearing(self, rp_name: str, rp_uuid: str) -> str:
        """Process clearing traits from a single provider"""
        current_traits = self.openstack_client.get_resource_provider_traits(rp_uuid)
        custom_traits_on_rp = self._filter_custom_traits(current_traits)

        if not custom_traits_on_rp:
            self.log(f"No CUSTOM traits found on {rp_name}")
            return "skip"

        self.log(
            f"Found {len(custom_traits_on_rp)} CUSTOM traits on {rp_name}: {custom_traits_on_rp}"
        )

        # Remove CUSTOM traits from resource provider
        non_custom_traits = self._filter_non_custom_traits(current_traits)

        # Set traits to only non-CUSTOM traits (effectively removing CUSTOM ones)
        return self._clear_traits_from_provider(
            rp_name, rp_uuid, non_custom_traits, len(custom_traits_on_rp)
        )

    def _filter_custom_traits(self, current_traits: List[str]) -> List[str]:
        """Filter custom traits from current traits"""
        return [trait for trait in current_traits if CPUUtils.is_custom_trait(trait)]

    def _filter_non_custom_traits(self, current_traits: List[str]) -> List[str]:
        """Filter non-custom traits from current traits"""
        return [
            trait for trait in current_traits if not CPUUtils.is_custom_trait(trait)
        ]

    def _clear_traits_from_provider(
        self,
        rp_name: str,
        rp_uuid: str,
        non_custom_traits: List[str],
        custom_traits_count: int,
    ) -> str:
        """Clear traits from provider and return result"""
        success = self.openstack_client.set_resource_provider_traits(
            rp_uuid, non_custom_traits
        )

        if success:
            print(f"  ✓ {rp_name:<60} (Cleared {custom_traits_count} CUSTOM traits)")
            return "success"
        print(f"  ✗ {rp_name:<60} (Failed to clear traits)")
        return "error"

    def _delete_custom_traits_from_placement(
        self, custom_traits: List[str]
    ) -> Dict[str, int]:
        """Delete CUSTOM traits from placement service and return results"""
        deleted_count = 0
        delete_error_count = 0

        self.log(
            f"Deleting {len(custom_traits)} CUSTOM traits from placement service..."
        )

        for trait_name in sorted(custom_traits):
            result = self._delete_single_trait(trait_name)
            if result == "success":
                deleted_count += 1
            elif result == "error":
                delete_error_count += 1

        return {
            "deleted_count": deleted_count,
            "delete_error_count": delete_error_count,
        }

    def _delete_single_trait(self, trait_name: str) -> str:
        """Delete a single trait from placement service"""
        try:
            response = self.openstack_client.make_placement_api_request(
                "DELETE", f"/traits/{trait_name}"
            )

            if response.status_code in self.openstack_client.SUCCESS_HTTP_CODES:
                print(f"  ✓ {trait_name:<60} (Deleted)")
                return "success"
            print(f"  ✗ {trait_name:<60} (Failed to delete: {response.status_code})")
            return "error"

        except Exception as e:
            self.log(f"Error deleting trait {trait_name}: {e}")
            print(f"  ✗ {trait_name:<60} (Error: {e})")
            return "error"

    def _print_clearing_summary(
        self, clear_results: Dict[str, int], delete_results: Dict[str, int]
    ) -> None:
        """Print summary of clearing operations"""
        print()
        print("Summary")

        summary_columns = ["Operation", "Status", "Count"]
        summary_rows = []

        if clear_results["cleared_count"] > 0:
            summary_rows.append(
                ["Clear from RPs", "Success", str(clear_results["cleared_count"])]
            )
        if clear_results["error_count"] > 0:
            summary_rows.append(
                ["Clear from RPs", "Errors", str(clear_results["error_count"])]
            )
        if delete_results["deleted_count"] > 0:
            summary_rows.append(
                ["Delete traits", "Success", str(delete_results["deleted_count"])]
            )
        if delete_results["delete_error_count"] > 0:
            summary_rows.append(
                ["Delete traits", "Errors", str(delete_results["delete_error_count"])]
            )

        TableUtils.print_table(summary_columns, summary_rows)
