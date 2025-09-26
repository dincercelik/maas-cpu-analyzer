"""Tests for documentation integration with build systems."""

import subprocess
from pathlib import Path

import pytest


class TestDocumentationIntegration:
    """Test documentation integration with Makefile and tox."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent

    def test_makefile_docs_target(self, project_root):
        """Test that Makefile docs target works."""
        # Check that Makefile exists
        makefile_path = project_root / "Makefile"
        assert makefile_path.exists(), "Makefile not found"

        # Read Makefile content
        makefile_content = makefile_path.read_text()

        # Check that docs target exists
        assert "docs:" in makefile_content, "docs target not found in Makefile"

        # Check that docs target has proper command
        assert (
            "sphinx-build" in makefile_content
        ), "sphinx-build command not found in docs target"

    def test_tox_docs_environment(self, project_root):
        """Test that tox docs environment is properly configured."""
        # Check that tox.ini exists
        tox_ini_path = project_root / "tox.ini"
        assert tox_ini_path.exists(), "tox.ini not found"

        # Read tox.ini content
        tox_content = tox_ini_path.read_text()

        # Check that docs environment exists
        assert "[testenv:docs]" in tox_content, "docs environment not found in tox.ini"

        # Check that docs environment has proper dependencies
        assert (
            "sphinx-build" in tox_content
        ), "sphinx-build command not found in docs environment"

        # Check that docs environment is in envlist
        envlist_section = ""
        in_envlist = False
        for line in tox_content.split("\n"):
            if line.strip() == "envlist =":
                in_envlist = True
                continue
            if in_envlist and line.strip().startswith("["):
                break
            if in_envlist:
                envlist_section += line

        assert "docs" in envlist_section, "docs environment not in envlist"

    def test_requirements_include_docs_dependencies(self, project_root):
        """Test that requirements-test.txt includes documentation dependencies."""
        requirements_path = project_root / "requirements-test.txt"
        assert requirements_path.exists(), "requirements-test.txt not found"

        requirements_content = requirements_path.read_text()

        # Check for required documentation dependencies
        required_deps = [
            "sphinx",
            "sphinx-rtd-theme",
            "myst-parser",
        ]

        for dep in required_deps:
            assert (
                dep in requirements_content
            ), f"Documentation dependency {dep} not found in requirements-test.txt"

    def test_docs_build_with_make(self, project_root):
        """Test that documentation can be built using make."""
        # Run make docs command
        result = subprocess.run(
            ["make", "docs"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,  # 5 minute timeout
        )

        # Check that the command succeeded
        assert result.returncode == 0, (
            f"make docs failed with return code {result.returncode}\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )

        # Check that output directory was created
        docs_build_dir = project_root / "docs" / "_build" / "html"
        assert docs_build_dir.exists(), "Documentation build directory not created"

        # Check that index.html exists
        index_file = docs_build_dir / "index.html"
        assert index_file.exists(), "index.html not generated"

    def test_docs_build_with_tox(self, project_root):
        """Test that documentation can be built using tox."""
        # Run tox docs command
        result = subprocess.run(
            ["tox", "-e", "docs"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=600,  # 10 minute timeout for tox
        )

        # Check that the command succeeded
        assert result.returncode == 0, (
            f"tox -e docs failed with return code {result.returncode}\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )

    def test_docs_clean_target(self, project_root):
        """Test that documentation can be cleaned."""
        # First build docs
        subprocess.run(
            ["make", "docs"],
            cwd=project_root,
            capture_output=True,
            check=False,
            timeout=300,
        )

        # Check that build directory exists
        docs_build_dir = project_root / "docs" / "_build"
        assert docs_build_dir.exists(), "Documentation build directory should exist"

        # Run make clean
        result = subprocess.run(
            ["make", "clean"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )

        # Check that clean succeeded
        assert result.returncode == 0, (
            f"make clean failed with return code {result.returncode}\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )

    def test_docs_directory_permissions(self, project_root):
        """Test that docs directory has proper permissions."""
        docs_dir = project_root / "docs"

        # Check that docs directory is readable
        assert docs_dir.is_dir(), "docs should be a directory"
        assert docs_dir.stat().st_mode & 0o444, "docs directory should be readable"

        # Check that conf.py is readable
        conf_py = docs_dir / "conf.py"
        assert conf_py.is_file(), "conf.py should be a file"
        assert conf_py.stat().st_mode & 0o444, "conf.py should be readable"

    def test_docs_static_directory(self, project_root):
        """Test that docs static directory exists and is properly configured."""
        docs_dir = project_root / "docs"
        static_dir = docs_dir / "_static"

        # Check that _static directory exists
        assert static_dir.exists(), "_static directory should exist"
        assert static_dir.is_dir(), "_static should be a directory"

        # Check conf.py references _static
        conf_py = docs_dir / "conf.py"
        conf_content = conf_py.read_text()
        assert "_static" in conf_content, "conf.py should reference _static directory"

    def test_docs_build_consistency(self, project_root):
        """Test that documentation builds consistently across different methods."""
        # Build docs with make
        result1 = subprocess.run(
            ["make", "docs"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )

        assert result1.returncode == 0, "make docs should succeed"

        # Clean and build with tox
        subprocess.run(
            ["make", "clean"],
            cwd=project_root,
            capture_output=True,
            check=False,
        )

        result2 = subprocess.run(
            ["tox", "-e", "docs"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=600,
        )

        assert result2.returncode == 0, "tox -e docs should succeed"

        # Both methods should produce the same result
        docs_build_dir = project_root / "docs" / "_build" / "html"
        index_file = docs_build_dir / "index.html"
        assert index_file.exists(), "index.html should exist after both build methods"

    def test_docs_build_with_warnings_as_errors(self, project_root):
        """Test that documentation build treats warnings as errors."""
        # This test ensures that the -W flag is used in the build commands
        makefile_path = project_root / "Makefile"
        makefile_content = makefile_path.read_text()

        # Check that make docs uses -W flag
        docs_section = ""
        in_docs_section = False
        for line in makefile_content.split("\n"):
            if line.strip().startswith("docs:"):
                in_docs_section = True
                continue
            if in_docs_section and line.strip() and not line.startswith("\t"):
                break
            if in_docs_section:
                docs_section += line + "\n"

        assert (
            "-W" in docs_section
        ), "make docs should use -W flag to treat warnings as errors"

        # Check that tox docs environment uses -W flag
        tox_ini_path = project_root / "tox.ini"
        tox_content = tox_ini_path.read_text()

        docs_env_section = ""
        in_docs_env = False
        for line in tox_content.split("\n"):
            if line.strip() == "[testenv:docs]":
                in_docs_env = True
                continue
            if (
                in_docs_env
                and line.strip().startswith("[")
                and line.strip() != "[testenv:docs]"
            ):
                break
            if in_docs_env:
                docs_env_section += line + "\n"

        assert "-W" in docs_env_section, "tox docs environment should use -W flag"
