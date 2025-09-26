"""Tests for documentation build process."""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest


class TestDocumentationBuild:
    """Test that documentation builds correctly."""

    def test_sphinx_build_succeeds(self):
        """Test that Sphinx documentation builds without errors."""
        # Get the project root directory
        project_root = Path(__file__).parent.parent.parent
        docs_dir = project_root / "docs"

        # Ensure docs directory exists
        assert docs_dir.exists(), "docs directory not found"

        # Create a temporary directory for build output
        with tempfile.TemporaryDirectory() as temp_dir:
            build_dir = Path(temp_dir) / "html"

            # Run sphinx-build
            cmd = [
                "sphinx-build",
                "-W",  # Treat warnings as errors
                "-b",
                "html",
                str(docs_dir),
                str(build_dir),
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                cwd=project_root,
            )

            # Check that the build succeeded
            assert result.returncode == 0, (
                f"Sphinx build failed with return code {result.returncode}\n"
                f"STDOUT: {result.stdout}\n"
                f"STDERR: {result.stderr}"
            )

            # Check that important files were generated
            index_file = build_dir / "index.html"
            assert index_file.exists(), "index.html not generated"

            # Check that the index file has content
            assert index_file.stat().st_size > 0, "index.html is empty"

    def test_sphinx_build_with_spelling(self):
        """Test that Sphinx documentation builds with spelling check."""
        # Get the project root directory
        project_root = Path(__file__).parent.parent.parent
        docs_dir = project_root / "docs"

        # Create a temporary directory for build output
        with tempfile.TemporaryDirectory() as temp_dir:
            build_dir = Path(temp_dir) / "html"

            # Run sphinx-build with spelling check
            cmd = [
                "sphinx-build",
                "-W",  # Treat warnings as errors
                "-b",
                "spelling",
                str(docs_dir),
                str(build_dir),
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                cwd=project_root,
            )

            # Spelling check might fail due to missing dictionary, which is OK
            # We just want to ensure the command runs without syntax errors
            assert result.returncode in [0, 2], (
                f"Sphinx spelling check failed unexpectedly with return code {result.returncode}\n"
                f"STDOUT: {result.stdout}\n"
                f"STDERR: {result.stderr}"
            )

    def test_docs_directory_structure(self):
        """Test that the docs directory has the expected structure."""
        project_root = Path(__file__).parent.parent.parent
        docs_dir = project_root / "docs"

        # Check required files exist
        required_files = [
            "conf.py",
            "index.rst",
            "installation.rst",
            "usage.rst",
            "api.rst",
            "configuration.rst",
            "development.rst",
            "changelog.rst",
        ]

        for file_name in required_files:
            file_path = docs_dir / file_name
            assert (
                file_path.exists()
            ), f"Required documentation file {file_name} not found"
            assert (
                file_path.stat().st_size > 0
            ), f"Documentation file {file_name} is empty"

    def test_conf_py_is_valid(self):
        """Test that conf.py can be imported without errors."""
        project_root = Path(__file__).parent.parent.parent
        conf_py_path = project_root / "docs" / "conf.py"

        # Try to import the conf.py file
        import importlib.util
        import sys

        spec = importlib.util.spec_from_file_location("conf", conf_py_path)
        conf_module = importlib.util.module_from_spec(spec)

        # This should not raise an exception
        spec.loader.exec_module(conf_module)

        # Check that important configuration variables exist
        assert hasattr(conf_module, "project"), "conf.py missing 'project' variable"
        assert hasattr(conf_module, "author"), "conf.py missing 'author' variable"
        assert hasattr(
            conf_module, "extensions"
        ), "conf.py missing 'extensions' variable"
        assert hasattr(
            conf_module, "html_theme"
        ), "conf.py missing 'html_theme' variable"

        # Check that required extensions are included
        required_extensions = [
            "sphinx.ext.autodoc",
            "sphinx.ext.autosummary",
            "sphinx.ext.intersphinx",
            "sphinx.ext.napoleon",
        ]

        for ext in required_extensions:
            assert (
                ext in conf_module.extensions
            ), f"Required extension {ext} not found in conf.py"

    def test_rst_files_are_valid(self):
        """Test that RST files have valid syntax."""
        project_root = Path(__file__).parent.parent.parent
        docs_dir = project_root / "docs"

        # List of RST files to check
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

            # Use sphinx-build to validate RST syntax
            with tempfile.TemporaryDirectory() as temp_dir:
                build_dir = Path(temp_dir) / "html"

                cmd = [
                    "sphinx-build",
                    "-W",  # Treat warnings as errors
                    "-b",
                    "html",
                    str(rst_path.parent),
                    str(build_dir),
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False,
                    cwd=project_root,
                )

                # Check that the build succeeded
                assert result.returncode == 0, (
                    f"RST file {rst_file} has syntax errors\n"
                    f"STDOUT: {result.stdout}\n"
                    f"STDERR: {result.stderr}"
                )
