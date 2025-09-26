"""Tests for documentation content validation."""

import re
from pathlib import Path

import pytest


class TestDocumentationContent:
    """Test documentation content for completeness and correctness."""

    @pytest.fixture
    def docs_dir(self):
        """Get the docs directory path."""
        project_root = Path(__file__).parent.parent.parent
        return project_root / "docs"

    def test_index_rst_content(self, docs_dir):
        """Test that index.rst has required content."""
        index_file = docs_dir / "index.rst"
        content = index_file.read_text()

        # Check for required sections
        required_sections = [
            "MAAS CPU Analyzer Documentation",
            "Features",
            "Quick Start",
            "toctree:",
            "installation",
            "usage",
            "api",
            "configuration",
            "development",
            "changelog",
        ]

        for section in required_sections:
            assert section in content, f"Missing required section: {section}"

    def test_installation_rst_content(self, docs_dir):
        """Test that installation.rst has required content."""
        installation_file = docs_dir / "installation.rst"
        content = installation_file.read_text()

        # Check for required sections
        required_sections = [
            "Installation",
            "Prerequisites",
            "Install from PyPI",
            "Install from Source",
            "Environment Setup",
            "Verification",
        ]

        for section in required_sections:
            assert section in content, f"Missing required section: {section}"

    def test_usage_rst_content(self, docs_dir):
        """Test that usage.rst has required content."""
        usage_file = docs_dir / "usage.rst"
        content = usage_file.read_text()

        # Check for required sections
        required_sections = [
            "Usage",
            "Command Line Interface",
            "Basic Usage",
            "Command Options",
            "Filtering Options",
            "Output Options",
            "Configuration",
            "Examples",
            "Troubleshooting",
        ]

        for section in required_sections:
            assert section in content, f"Missing required section: {section}"

    def test_api_rst_content(self, docs_dir):
        """Test that api.rst has required content."""
        api_file = docs_dir / "api.rst"
        content = api_file.read_text()

        # Check for required sections
        required_sections = [
            "API Reference",
            "Core Modules",
            "MAAS CPU Analyzer",
            "MAAS Client",
            "OpenStack Client",
            "Trait Manager",
            "Utilities",
            "Utility Classes",
            "Configuration",
            "Logging",
        ]

        for section in required_sections:
            assert section in content, f"Missing required section: {section}"

    def test_configuration_rst_content(self, docs_dir):
        """Test that configuration.rst has required content."""
        config_file = docs_dir / "configuration.rst"
        content = config_file.read_text()

        # Check for required sections
        required_sections = [
            "Configuration",
            "Environment Variables",
            "MAAS Configuration",
            "OpenStack Configuration",
            "Network Configuration",
            "Command-Line Arguments",
            "Example Configurations",
            "Security Considerations",
        ]

        for section in required_sections:
            assert section in content, f"Missing required section: {section}"

    def test_development_rst_content(self, docs_dir):
        """Test that development.rst has required content."""
        dev_file = docs_dir / "development.rst"
        content = dev_file.read_text()

        # Check for required sections
        required_sections = [
            "Development",
            "Getting Started",
            "Project Structure",
            "Development Commands",
            "Testing",
            "Code Quality",
            "Documentation",
            "Contributing",
        ]

        for section in required_sections:
            assert section in content, f"Missing required section: {section}"

    def test_changelog_rst_content(self, docs_dir):
        """Test that changelog.rst has required content."""
        changelog_file = docs_dir / "changelog.rst"
        content = changelog_file.read_text()

        # Check for required sections
        required_sections = [
            "Changelog",
            "[Unreleased]",
            "Added",
            "Changed",
            "Deprecated",
            "Removed",
            "Fixed",
            "Security",
            "[1.0.0]",
        ]

        for section in required_sections:
            assert section in content, f"Missing required section: {section}"

    def test_rst_files_have_proper_headers(self, docs_dir):
        """Test that RST files have proper header formatting."""
        rst_files = [
            "index.rst",
            "installation.rst",
            "usage.rst",
            "api.rst",
            "configuration.rst",
            "development.rst",
            "changelog.rst",
        ]

        for rst_file in rst_files:
            rst_path = docs_dir / rst_file
            content = rst_path.read_text()

            # Check that the file has a proper title
            lines = content.split("\n")
            assert len(lines) >= 2, f"{rst_file} should have at least 2 lines"

            title = lines[0].strip()
            underline = lines[1].strip()

            # Check that title is not empty
            assert title, f"{rst_file} has empty title"

            # Check that underline matches title length
            assert len(underline) >= len(title), f"{rst_file} underline too short"

            # Check that underline consists of valid RST characters
            valid_chars = set("=-~^\"'`:.")
            assert all(
                c in valid_chars for c in underline
            ), f"{rst_file} has invalid underline characters"

    def test_code_blocks_are_properly_formatted(self, docs_dir):
        """Test that code blocks are properly formatted."""
        rst_files = [
            "installation.rst",
            "usage.rst",
            "configuration.rst",
            "development.rst",
        ]

        for rst_file in rst_files:
            rst_path = docs_dir / rst_file
            content = rst_path.read_text()

            # Check for properly formatted code blocks
            code_block_pattern = r"\.\. code-block::\s+\w+"
            code_blocks = re.findall(code_block_pattern, content)

            # Each code block should have a language specified
            for block in code_blocks:
                assert (
                    "bash" in block or "python" in block or "text" in block
                ), f"{rst_file} has code block without proper language: {block}"

    def test_environment_variables_are_documented(self, docs_dir):
        """Test that all important environment variables are documented."""
        config_file = docs_dir / "configuration.rst"
        content = config_file.read_text()

        # Check for required environment variables
        required_env_vars = [
            "MAAS_URL",
            "MAAS_API_KEY",
            "OS_AUTH_URL",
            "OS_USERNAME",
            "OS_PASSWORD",
            "OS_PROJECT_NAME",
        ]

        for env_var in required_env_vars:
            assert (
                env_var in content
            ), f"Environment variable {env_var} not documented in configuration.rst"

    def test_command_line_options_are_documented(self, docs_dir):
        """Test that command line options are documented."""
        usage_file = docs_dir / "usage.rst"
        content = usage_file.read_text()

        # Check for command line options
        required_options = [
            "--zone",
            "--deployed-only",
            "--tags",
            "--verbose",
            "--version",
            "--help",
        ]

        for option in required_options:
            assert (
                option in content
            ), f"Command line option {option} not documented in usage.rst"

    def test_links_are_valid(self, docs_dir):
        """Test that internal links are valid."""
        # This is a basic check - in a real scenario, you might want to
        # use a tool like linkchecker or sphinx-linkcheck
        rst_files = [
            "index.rst",
            "installation.rst",
            "usage.rst",
            "api.rst",
            "configuration.rst",
            "development.rst",
        ]

        for rst_file in rst_files:
            rst_path = docs_dir / rst_file
            content = rst_path.read_text()

            # Check for internal references (they should use proper RST syntax)
            # Look for patterns like :ref:`something` or :doc:`something`
            ref_pattern = r":ref:`([^`]+)`"
            doc_pattern = r":doc:`([^`]+)`"

            refs = re.findall(ref_pattern, content)
            docs = re.findall(doc_pattern, content)

            # Basic validation - references should not be empty
            for ref in refs:
                assert ref.strip(), f"{rst_file} has empty reference: {ref}"

            for doc in docs:
                assert doc.strip(), f"{rst_file} has empty doc reference: {doc}"

    def test_no_broken_rst_syntax(self, docs_dir):
        """Test that RST files don't have obvious syntax errors."""
        rst_files = [
            "index.rst",
            "installation.rst",
            "usage.rst",
            "api.rst",
            "configuration.rst",
            "development.rst",
            "changelog.rst",
        ]

        for rst_file in rst_files:
            rst_path = docs_dir / rst_file
            content = rst_path.read_text()

            # Check for common RST syntax issues
            lines = content.split("\n")

            for i, line in enumerate(lines, 1):
                # Check for unterminated code blocks
                if line.strip().startswith(".. code-block::"):
                    # Look for the next non-empty line
                    j = i
                    while j < len(lines) and not lines[j].strip():
                        j += 1

                    if j < len(lines):
                        next_line = lines[j]
                        # Should start with proper indentation or be empty
                        if next_line.strip() and not next_line.startswith((" ", "\t")):
                            pytest.fail(
                                f"{rst_file}:{j + 1} Code block not properly indented"
                            )

    def test_documentation_completeness(self, docs_dir):
        """Test that documentation covers all major features."""
        # Read all documentation content
        all_content = ""
        rst_files = [
            "index.rst",
            "installation.rst",
            "usage.rst",
            "api.rst",
            "configuration.rst",
            "development.rst",
            "changelog.rst",
        ]

        for rst_file in rst_files:
            rst_path = docs_dir / rst_file
            all_content += rst_path.read_text() + "\n"

        # Check for key features mentioned
        key_features = [
            "CPU analysis",
            "trait management",
            "OpenStack",
            "MAAS",
            "filtering",
            "logging",
            "security",
            "testing",
        ]

        for feature in key_features:
            assert (
                feature.lower() in all_content.lower()
            ), f"Key feature '{feature}' not mentioned in documentation"
