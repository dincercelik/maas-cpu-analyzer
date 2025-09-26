"""
Utility functions for MAAS CPU Analyzer.

This module contains common utility functions used across the application.
"""

import re
import sys
from typing import Dict, List

from prettytable import PrettyTable


class CPUUtils:
    """Utility class for CPU-related operations"""

    # Compiled regex patterns for better performance
    _INTEL_AMD_PATTERN = re.compile(r"(intel|amd)", re.IGNORECASE)
    _CUSTOM_TRAIT_PATTERN = re.compile(r"^CUSTOM_[A-Z0-9_]+$")

    @classmethod
    def get_cpu_vendor(cls, cpu_model: str) -> str:
        """Get CPU vendor from CPU model string"""
        if not cpu_model:
            return "UNKNOWN"

        cpu_model_lower = cpu_model.lower()
        if "intel" in cpu_model_lower:
            return "INTEL"
        if "amd" in cpu_model_lower:
            return "AMD"
        return "UNKNOWN"

    @classmethod
    def generate_trait_name(cls, cpu_model: str) -> str:
        """Generate OpenStack trait name from CPU model"""
        if not cpu_model:
            return "CUSTOM_UNKNOWN_EMPTY"

        # Clean and normalize the CPU model
        trait_name = cpu_model.strip()

        # Replace spaces and special characters with underscores
        trait_name = re.sub(r"[^A-Za-z0-9]", "_", trait_name)

        # Remove multiple consecutive underscores
        trait_name = re.sub(r"_+", "_", trait_name)

        # Remove leading/trailing underscores
        trait_name = trait_name.strip("_")

        # Convert to uppercase
        trait_name = trait_name.upper()

        # Remove trailing generic words like CPU or PROCESSOR
        trait_name = re.sub(r"_(CPU|PROCESSOR)$", "", trait_name)

        # Ensure it starts with CUSTOM_
        if not trait_name.startswith("CUSTOM_"):
            trait_name = f"CUSTOM_{trait_name}"

        # If vendor is unknown, ensure CUSTOM_UNKNOWN_ prefix
        vendor = cls.get_cpu_vendor(cpu_model)
        if vendor == "UNKNOWN":
            trait_name = trait_name.replace("CUSTOM_", "CUSTOM_UNKNOWN_", 1)

        # Ensure it's not too long (OpenStack trait name limit)
        if len(trait_name) > 255:
            return trait_name[:255]

        return trait_name

    @classmethod
    def is_intel_amd_cpu(cls, cpu_model: str) -> bool:
        """Check if CPU model is Intel or AMD"""
        return bool(cls._INTEL_AMD_PATTERN.search(cpu_model))

    @classmethod
    def is_custom_trait(cls, trait_name: str) -> bool:
        """Check if trait name matches custom trait pattern"""
        return bool(cls._CUSTOM_TRAIT_PATTERN.match(trait_name))


class TableUtils:
    """Utility class for table operations"""

    @staticmethod
    def print_table(columns: List[str], rows: List[List[str]]) -> None:
        """Print a table using PrettyTable"""
        if not columns or not rows:
            return

        table = PrettyTable(columns)
        table.align = "l"
        for row in rows:
            table.add_row(row)
        print(table)

    @staticmethod
    def build_machine_table_columns(should_create_openstack_traits: bool) -> List[str]:
        """Build table columns based on configuration"""
        if should_create_openstack_traits:
            return [
                "Hostname",
                "Zone",
                "Status",
                "Vendor",
                "CPU Model",
                "OpenStack Trait",
            ]
        return ["Hostname", "Zone", "Status", "Vendor", "CPU Model"]

    @staticmethod
    def build_machine_row(
        machine: Dict, should_create_openstack_traits: bool
    ) -> List[str]:
        """Build a single machine row"""
        hostname = machine.get("hostname", "unknown")
        machine_zone = machine.get("zone", {}).get("name", "unknown")
        status = machine.get("status_name", "unknown")
        cpu_model = machine.get("hardware_info", {}).get("cpu_model", "")
        vendor = CPUUtils.get_cpu_vendor(cpu_model)

        if should_create_openstack_traits:
            trait_name = CPUUtils.generate_trait_name(cpu_model)
            return [hostname, machine_zone, status, vendor, cpu_model, trait_name]
        return [hostname, machine_zone, status, vendor, cpu_model]


class MessageUtils:
    """Utility class for message formatting"""

    @staticmethod
    def format_processing_message(
        zone: str, deployed_only: bool, tags: List[str]
    ) -> str:
        """Format processing message"""
        status_msg = "deployed" if deployed_only else "all"
        tags_msg = f" with tags: {', '.join(tags)}" if tags else ""
        zone_msg = f" in zone: {zone}" if zone else " (all zones)"
        return f"Processing {status_msg} machines{zone_msg}{tags_msg}"

    @staticmethod
    def format_no_machines_message(zone: str) -> str:
        """Format no machines found message"""
        zone_msg = f" in zone: {zone}" if zone else ""
        return f"No machines found with Intel or AMD CPUs{zone_msg}."

    @staticmethod
    def format_distribution_title(zone: str, deployed_only: bool) -> str:
        """Format distribution table title"""
        status_text = "Deployed Machines Only" if deployed_only else "All Machines"
        zone_text = f" in {zone}" if zone else " (All Zones)"
        return f"CPU Model Distribution ({status_text}{zone_text})"


class MachineFilterUtils:
    """Utility class for machine filtering operations"""

    @staticmethod
    def filter_machines(
        machines: List[Dict], zone: str, deployed_only: bool, tags: List[str]
    ) -> List[Dict]:
        """Filter machines based on zone, deployment status, and tags"""
        filtered_machines = []
        for machine in machines:
            if MachineFilterUtils._should_include_machine(
                machine, zone, deployed_only, tags
            ):
                filtered_machines.append(machine)
        return filtered_machines

    @staticmethod
    def _should_include_machine(
        machine: Dict, zone: str, deployed_only: bool, tags: List[str]
    ) -> bool:
        """Check if machine should be included in filtered results"""
        if not MachineFilterUtils._matches_zone_filter(machine, zone):
            return False
        if not MachineFilterUtils._matches_deployment_filter(machine, deployed_only):
            return False
        if not MachineFilterUtils._matches_tags_filter(machine, tags):
            return False
        return True

    @staticmethod
    def _matches_zone_filter(machine: Dict, zone: str) -> bool:
        """Check if machine matches zone filter"""
        if not zone:
            return True
        machine_zone = machine.get("zone", {}).get("name", "")
        return machine_zone == zone

    @staticmethod
    def _matches_deployment_filter(machine: Dict, deployed_only: bool) -> bool:
        """Check if machine matches deployment filter"""
        if not deployed_only:
            return True
        status = machine.get("status_name", "")
        return status == "Deployed"

    @staticmethod
    def _matches_tags_filter(machine: Dict, tags: List[str]) -> bool:
        """Check if machine matches tags filter"""
        if not tags:
            return True
        machine_tags = machine.get("tag_names", [])
        return any(tag in machine_tags for tag in tags)


class ValidationUtils:
    """Utility class for validation operations"""

    @staticmethod
    def validate_hypervisor_assignment_requirement(args) -> None:
        """Validate that hypervisor assignment requires trait creation"""
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

    @staticmethod
    def validate_clear_traits_conflicts(args) -> None:
        """Validate that clear traits doesn't conflict with other options"""
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
