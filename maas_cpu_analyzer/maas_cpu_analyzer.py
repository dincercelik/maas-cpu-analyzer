"""
MAAS CPU Analyzer - Final optimized main module

This is the main module that orchestrates the CPU analysis workflow.
It has been optimized for maintainability by using separate modules.
"""

import argparse
import sys
from collections import Counter
from typing import Dict, List, Optional

from .maas_client import MAASClient
from .openstack_client import OpenStackClient
from .trait_manager import TraitManager
from .utils import (
    CPUUtils,
    MachineFilterUtils,
    MessageUtils,
    TableUtils,
    ValidationUtils,
)


class MAASCPUAnalyzer:
    """Main analyzer class that orchestrates the CPU analysis workflow"""

    def __init__(self, verbose: bool = False):
        """Initialize the analyzer"""
        self.verbose = verbose
        self.tags: List[str] = []
        self.should_create_openstack_traits = False
        self.assign_traits_to_hypervisors = False

        # Initialize clients
        self.openstack_client = OpenStackClient(verbose)
        self.maas_client = MAASClient(verbose)
        self.trait_manager = TraitManager(self.openstack_client, verbose, analyzer=self)

    def log(self, message: str) -> None:
        """Log message if verbose mode is enabled"""
        if self.verbose:
            print(f"[MAAS-CPU-Analyzer] {message}")

    # ---------------------------------------------------------------------
    # Backward-compatibility wrappers for tests and public API stability
    # ---------------------------------------------------------------------
    def get_cpu_vendor(self, cpu_model: str) -> str:
        """Delegate to CPUUtils.get_cpu_vendor"""
        return CPUUtils.get_cpu_vendor(cpu_model)

    def generate_trait_name(self, cpu_model: str) -> str:
        """Delegate to CPUUtils.generate_trait_name"""
        return CPUUtils.generate_trait_name(cpu_model)

    def fetch_maas_data(self) -> List[Dict]:
        """Delegate to MAASClient.fetch_maas_data"""
        return self.maas_client.fetch_maas_data()

    def _check_openstack_connectivity(self) -> bool:
        """Delegate to OpenStackClient.check_openstack_connectivity"""
        return self.openstack_client.check_openstack_connectivity()

    def _create_trait(self, trait_name: str) -> tuple[bool, str]:
        """Delegate to OpenStackClient.create_trait"""
        return self.openstack_client.create_trait(trait_name)

    def _get_resource_providers(self) -> List[Dict]:
        """Delegate to OpenStackClient.get_resource_providers"""
        return self.openstack_client.get_resource_providers()

    def _make_placement_api_request(
        self, method: str, endpoint: str, data: Optional[Dict] = None
    ):
        """Delegate to OpenStackClient.make_placement_api_request"""
        return self.openstack_client.make_placement_api_request(method, endpoint, data)

    def _get_hypervisors(self) -> List[Dict]:
        """Delegate to OpenStackClient.get_hypervisors"""
        return self.openstack_client.get_hypervisors()

    def print_machine_table(
        self, machines: List[Dict], zone: str, deployed_only: bool
    ) -> None:
        """Print the main machine table using PrettyTable"""
        filtered_machines = MachineFilterUtils.filter_machines(
            machines, zone, deployed_only, self.tags
        )

        # Filter for Intel/AMD CPUs only using compiled pattern
        cpu_machines = self._filter_cpu_machines(filtered_machines)
        if not cpu_machines:
            print(MessageUtils.format_no_machines_message(zone))
            return

        print(MessageUtils.format_processing_message(zone, deployed_only, self.tags))

        columns = TableUtils.build_machine_table_columns(
            self.should_create_openstack_traits
        )
        rows = [
            TableUtils.build_machine_row(machine, self.should_create_openstack_traits)
            for machine in cpu_machines
        ]

        TableUtils.print_table(columns, rows)

    def _filter_cpu_machines(self, filtered_machines: List[Dict]) -> List[Dict]:
        """Filter machines for Intel/AMD CPUs only"""
        cpu_machines = []
        for machine in filtered_machines:
            cpu_model = machine.get("hardware_info", {}).get("cpu_model", "")
            if CPUUtils.is_intel_amd_cpu(cpu_model):
                cpu_machines.append(machine)
        return cpu_machines

    def print_cpu_distribution(
        self, machines: List[Dict], zone: str, deployed_only: bool
    ) -> None:
        """Print CPU model distribution using PrettyTable"""
        print()
        self.log("Generating CPU model histogram")

        # Get CPU models from filtered machines
        cpu_models = self._extract_cpu_models_from_machines(
            machines, zone, deployed_only
        )
        if not cpu_models:
            return

        # Generate and print distribution
        self._print_cpu_distribution_table(cpu_models, zone, deployed_only)

    def _extract_cpu_models_from_machines(
        self, machines: List[Dict], zone: str, deployed_only: bool
    ) -> List[str]:
        """Extract CPU models from filtered machines"""
        filtered_machines = MachineFilterUtils.filter_machines(
            machines, zone, deployed_only, self.tags
        )
        cpu_models = []

        for machine in filtered_machines:
            cpu_model = machine.get("hardware_info", {}).get("cpu_model", "")
            if CPUUtils.is_intel_amd_cpu(cpu_model):
                cpu_models.append(cpu_model)

        return cpu_models

    def _print_cpu_distribution_table(
        self, cpu_models: List[str], zone: str, deployed_only: bool
    ) -> None:
        """Print CPU distribution table"""
        # Use Counter for efficient counting
        model_counts = Counter(cpu_models)
        sorted_models = model_counts.most_common()

        # Generate title
        title = MessageUtils.format_distribution_title(zone, deployed_only)
        print(title)

        # Create table
        columns = ["Count", "CPU Model"]
        rows = [[str(count), model] for model, count in sorted_models]

        TableUtils.print_table(columns, rows)

    def create_openstack_traits(
        self, machines: List[Dict], zone: str, deployed_only: bool
    ) -> None:
        """Create OpenStack traits from CPU models"""
        if not self.should_create_openstack_traits:
            return

        self.trait_manager.create_traits_from_machines(
            machines, zone, deployed_only, self.tags
        )

    def assign_cpu_traits_to_hypervisors(
        self, machines: List[Dict], zone: str, deployed_only: bool
    ) -> None:
        """Assign CPU traits to OpenStack hypervisors based on MAAS machine CPU models"""
        if not self.assign_traits_to_hypervisors:
            return

        # Informative header for integration tests and users
        print("Assigning CPU Traits to Hypervisors")

        self.trait_manager.assign_traits_to_hypervisors(
            machines, zone, deployed_only, self.tags
        )

    def clear_openstack_traits(self) -> None:
        """Clear all CUSTOM traits from OpenStack hypervisors and delete the traits"""
        self.trait_manager.clear_openstack_traits()

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

        machines = self.fetch_maas_data()
        self.print_machine_table(machines, zone, deployed_only)
        self.print_cpu_distribution(machines, zone, deployed_only)
        self.create_openstack_traits(machines, zone, deployed_only)

        if self.assign_traits_to_hypervisors:
            self.assign_cpu_traits_to_hypervisors(machines, zone, deployed_only)

        self.log("Script completed successfully")
        # Also mirror completion message to stderr for compatibility with tests (only when verbose)
        if self.verbose:
            print("Script completed successfully", file=sys.stderr)


def main():
    """Main entry point"""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Validate arguments
    validate_arguments(args)

    # Parse and prepare arguments
    deployed_only = args.deployed_only
    tags = parse_tags_argument(args.tags)

    # Create analyzer and run
    analyzer = MAASCPUAnalyzer(verbose=args.verbose)
    analyzer.run(
        args.zone,
        deployed_only,
        tags,
        args.create_openstack_traits,
        args.assign_traits_to_hypervisors,
        args.clear_openstack_traits,
    )


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser"""
    parser = argparse.ArgumentParser(
        description="MAAS CPU Analyzer - Analyze CPU models in MAAS machines and optionally create OpenStack traits for resource scheduling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=get_help_epilog(),
    )

    add_arguments_to_parser(parser)
    return parser


def get_help_epilog() -> str:
    """Get help epilog text"""
    return """
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
        """


def add_arguments_to_parser(parser: argparse.ArgumentParser) -> None:
    """Add arguments to the parser"""
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


def validate_arguments(args) -> None:
    """Validate command line arguments"""
    ValidationUtils.validate_hypervisor_assignment_requirement(args)
    ValidationUtils.validate_clear_traits_conflicts(args)


def parse_tags_argument(tags_arg: Optional[str]) -> List[str]:
    """Parse tags argument into list"""
    if tags_arg:
        return [tag.strip() for tag in tags_arg.split(",") if tag.strip()]
    return []


if __name__ == "__main__":
    main()
