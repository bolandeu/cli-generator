"""Fixture packages for the gate's tests (tests/ and standard/tests/), built in tmp_path.

A package: git, a pyproject.toml, uv.lock, a module, a test, and the files the Standard asks for (README.md,
AGENTS.md, no workflow). Its ruff, ty and pytest are this repo's own, found on PATH
(`uv run` in a package without them falls back to PATH).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

PYPROJECT = """[project]
name = "demo"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.rb.install]
homeserver = []
mac = false
"""


def git(root: Path, *args: str) -> None:
    subprocess.run(  # noqa: S603
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],  # noqa: S607
        cwd=root,
        capture_output=True,
        check=True,
    )


def _package(root: Path, module: str, pyproject: str) -> Path:
    (root / "src" / "demo").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "pyproject.toml").write_text(pyproject)
    (root / ".gitignore").write_text(".venv/\n__pycache__/\n")
    (root / "README.md").write_text("# demo\n")
    (root / "AGENTS.md").write_text("# demo\n")
    (root / "src" / "demo" / "__init__.py").write_text(module)
    (root / "tests" / "test_demo.py").write_text("def test_demo() -> None:\n    assert True\n")
    subprocess.run(["uv", "lock", "--offline", "--quiet"], cwd=root, check=True)  # noqa: S607
    git(root, "init", "-q", "-b", "main")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "init")
    return root


@pytest.fixture
def in_package(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    def make(module: str, pyproject: str = PYPROJECT) -> Path:
        root = _package(tmp_path / "demo", module, pyproject)
        monkeypatch.chdir(root)
        return root

    tools = str(Path(sys.executable).parent)  # this repo's ruff, ty, pytest
    monkeypatch.setenv("PATH", f"{tools}{os.pathsep}{os.environ['PATH']}")
    return make
