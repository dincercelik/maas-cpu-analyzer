"""Tests for documentation quality and performance."""

import os
import subprocess
from pathlib import Path

import pytest


class TestDocumentationQuality:
    """Test documentation quality, performance, and accessibility."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def built_docs_dir(self, project_root):
        """Build documentation and return the build directory."""
        # Build docs
        result = subprocess.run(
            ["make", "docs"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )

        assert result.returncode == 0, f"Failed to build docs: {result.stderr}"

        return project_root / "docs" / "_build" / "html"

    def test_docs_build_performance(self, project_root):
        """Test that documentation builds in reasonable time."""
        import time

        start_time = time.time()

        result = subprocess.run(
            ["make", "docs"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )

        end_time = time.time()
        build_time = end_time - start_time

        # Documentation should build in less than 5 minutes
        assert (
            build_time < 300
        ), f"Documentation build took too long: {build_time:.2f} seconds"

        # Should succeed
        assert result.returncode == 0, f"Documentation build failed: {result.stderr}"

    def test_docs_file_sizes(self, built_docs_dir):
        """Test that documentation files are reasonably sized."""
        # Check that index.html exists and is not empty
        index_file = built_docs_dir / "index.html"
        assert index_file.exists(), "index.html should exist"

        index_size = index_file.stat().st_size
        assert index_size > 1000, "index.html should be substantial (>1KB)"
        assert index_size < 1000000, "index.html should not be too large (<1MB)"

    def test_docs_html_validity(self, built_docs_dir):
        """Test that generated HTML is valid."""
        # This is a basic check - in a real scenario, you might want to use
        # html5validator or similar tools
        html_files = list(built_docs_dir.glob("*.html"))
        assert len(html_files) > 0, "No HTML files generated"

        # Check that HTML files contain basic HTML structure
        for html_file in html_files:
            content = html_file.read_text()

            # Should contain basic HTML tags
            assert "<html" in content.lower(), f"{html_file.name} missing <html> tag"
            assert "<head" in content.lower(), f"{html_file.name} missing <head> tag"
            assert "<body" in content.lower(), f"{html_file.name} missing <body> tag"

            # Should not contain obvious HTML errors
            assert (
                "&lt;" not in content or "&gt;" not in content
            ), f"{html_file.name} may contain unescaped HTML entities"

    def test_docs_css_and_js_included(self, built_docs_dir):
        """Test that CSS and JavaScript files are included."""
        static_dir = built_docs_dir / "_static"
        assert static_dir.exists(), "_static directory should exist"

        # Check for basic CSS files
        css_files = list(static_dir.glob("*.css"))
        assert len(css_files) > 0, "No CSS files found in _static"

        # Check for basic JS files
        js_files = list(static_dir.glob("*.js"))
        assert len(js_files) > 0, "No JavaScript files found in _static"

    def test_docs_search_functionality(self, built_docs_dir):
        """Test that search functionality is available."""
        # Check that search index files exist
        search_index = built_docs_dir / "searchindex.js"
        assert (
            search_index.exists()
        ), "searchindex.js should exist for search functionality"

        # Check that search page exists
        search_page = built_docs_dir / "search.html"
        assert search_page.exists(), "search.html should exist"

    def test_docs_navigation_structure(self, built_docs_dir):
        """Test that documentation has proper navigation structure."""
        index_file = built_docs_dir / "index.html"
        content = index_file.read_text()

        # Should contain navigation elements
        nav_elements = [
            "installation.html",
            "usage.html",
            "api.html",
            "configuration.html",
            "development.html",
            "changelog.html",
        ]

        for nav_element in nav_elements:
            assert nav_element in content, f"Navigation link to {nav_element} not found"

    def test_docs_mobile_responsive(self, built_docs_dir):
        """Test that documentation is mobile responsive."""
        index_file = built_docs_dir / "index.html"
        content = index_file.read_text()

        # Should contain viewport meta tag for mobile responsiveness
        assert (
            "viewport" in content.lower()
        ), "Missing viewport meta tag for mobile responsiveness"

    def test_docs_accessibility_basics(self, built_docs_dir):
        """Test basic accessibility features."""
        html_files = list(built_docs_dir.glob("*.html"))

        for html_file in html_files:
            content = html_file.read_text()

            # Should have proper heading structure
            if "installation" in html_file.name:
                assert "<h1" in content, f"{html_file.name} should have h1 heading"

            # Should have alt attributes for images (if any)
            if "<img" in content:
                # This is a basic check - proper accessibility testing would be more comprehensive
                assert (
                    "alt=" in content
                ), f"{html_file.name} has images without alt attributes"

    def test_docs_no_broken_internal_links(self, built_docs_dir):
        """Test that internal links are not broken."""
        # Get all HTML files
        html_files = list(built_docs_dir.glob("*.html"))

        # Collect all internal links
        internal_links = set()
        for html_file in html_files:
            content = html_file.read_text()
            # Look for href attributes pointing to other HTML files
            import re

            links = re.findall(r'href="([^"]*\.html[^"]*)"', content)
            internal_links.update(links)

        # Check that all internal links point to existing files
        for link in internal_links:
            # Skip external links
            if link.startswith("http://") or link.startswith("https://"):
                continue

            # Handle fragment links
            if "#" in link:
                link = link.split("#")[0]

            if link:  # Skip empty links
                target_file = built_docs_dir / link
                assert target_file.exists(), f"Broken internal link: {link}"

    def test_docs_metadata_completeness(self, built_docs_dir):
        """Test that documentation has proper metadata."""
        index_file = built_docs_dir / "index.html"
        content = index_file.read_text()

        # Should contain title
        assert "<title>" in content, "HTML should have title tag"

        # Should contain description or meta description
        assert (
            "description" in content.lower() or "meta" in content.lower()
        ), "HTML should have description metadata"

    def test_docs_build_reproducibility(self, project_root):
        """Test that documentation builds are reproducible."""
        # Build docs twice and compare
        subprocess.run(
            ["make", "clean"],
            cwd=project_root,
            capture_output=True,
            check=False,
        )

        # First build
        result1 = subprocess.run(
            ["make", "docs"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )
        assert result1.returncode == 0, "First build should succeed"

        # Get file sizes from first build
        docs_dir1 = project_root / "docs" / "_build" / "html"
        file_sizes1 = {}
        for html_file in docs_dir1.glob("*.html"):
            file_sizes1[html_file.name] = html_file.stat().st_size

        # Clean and build again
        subprocess.run(
            ["make", "clean"],
            cwd=project_root,
            capture_output=True,
            check=False,
        )

        result2 = subprocess.run(
            ["make", "docs"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )
        assert result2.returncode == 0, "Second build should succeed"

        # Get file sizes from second build
        docs_dir2 = project_root / "docs" / "_build" / "html"
        file_sizes2 = {}
        for html_file in docs_dir2.glob("*.html"):
            file_sizes2[html_file.name] = html_file.stat().st_size

        # File sizes should be the same (allowing for small differences)
        for filename, size1 in file_sizes1.items():
            if filename in file_sizes2:
                size_diff = abs(size1 - file_sizes2[filename])
                size_ratio = size_diff / max(size1, 1)
                assert (
                    size_ratio < 0.1
                ), f"File {filename} size differs significantly between builds"

    def test_docs_error_handling(self, project_root):
        """Test that documentation build handles errors gracefully."""
        # This test ensures that the build process doesn't crash on minor issues
        result = subprocess.run(
            ["make", "docs"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )

        # Build should succeed even if there are warnings
        assert (
            result.returncode == 0
        ), f"Documentation build should not fail: {result.stderr}"

        # Check that error output is reasonable
        if result.stderr:
            # Should not contain critical errors
            critical_errors = [
                "FATAL",
                "CRITICAL",
                "SEGFAULT",
                "CRASH",
            ]

            for error in critical_errors:
                assert (
                    error not in result.stderr.upper()
                ), f"Documentation build contains critical error: {error}"
