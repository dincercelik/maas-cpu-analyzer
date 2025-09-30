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
        makefile_path = project_root / "Makefile"
        assert makefile_path.exists(), "Makefile not found"

        makefile_content = makefile_path.read_text()
        assert "docs:" in makefile_content, "docs target not found in Makefile"
        assert (
            "sphinx-build" in makefile_content
        ), "sphinx-build command not found in docs target"

    def test_requirements_include_docs_dependencies(self, project_root):
        """Test that requirements-test.txt includes documentation dependencies."""
        requirements_path = project_root / "requirements-test.txt"
        assert requirements_path.exists(), "requirements-test.txt not found"

        requirements_content = requirements_path.read_text()
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
        result = subprocess.run(
            ["make", "docs"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )
        assert result.returncode == 0, (
            f"make docs failed with return code {result.returncode}\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )
        docs_build_dir = project_root / "docs" / "_build" / "html"
        assert docs_build_dir.exists(), "Documentation build directory not created"
        index_file = docs_build_dir / "index.html"
        assert index_file.exists(), "index.html not generated"

    def test_docs_clean_target(self, project_root):
        """Test that documentation can be cleaned."""
        subprocess.run(
            ["make", "docs"],
            cwd=project_root,
            capture_output=True,
            check=False,
            timeout=300,
        )
        docs_build_dir = project_root / "docs" / "_build"
        assert docs_build_dir.exists(), "Documentation build directory should exist"
        result = subprocess.run(
            ["make", "clean"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, (
            f"make clean failed with return code {result.returncode}\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )

    def test_docs_directory_permissions(self, project_root):
        """Test that docs directory has proper permissions."""
        docs_dir = project_root / "docs"
        assert docs_dir.is_dir(), "docs should be a directory"
        assert docs_dir.stat().st_mode & 0o444, "docs directory should be readable"
        conf_py = docs_dir / "conf.py"
        assert conf_py.is_file(), "conf.py should be a file"
        assert conf_py.stat().st_mode & 0o444, "conf.py should be readable"

    def test_docs_static_directory(self, project_root):
        """Test that docs static directory exists and is properly configured."""
        docs_dir = project_root / "docs"
        static_dir = docs_dir / "_static"
        assert static_dir.exists(), "_static directory should exist"
        assert static_dir.is_dir(), "_static should be a directory"
        conf_py = docs_dir / "conf.py"
        conf_content = conf_py.read_text()
        assert "_static" in conf_content, "conf.py should reference _static directory"

    def test_docs_build_with_warnings_as_errors(self, project_root):
        """Test that documentation build treats warnings as errors."""
        makefile_path = project_root / "Makefile"
        makefile_content = makefile_path.read_text()
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
