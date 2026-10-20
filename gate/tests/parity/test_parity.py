"""`rb-release check` is the same gate as the template's scripts/release.py (its last copy: template v1.20.10).

Both run in tmp_path copies of the fixture projects in tests/data/parity, with the same git state. Compared: the lines
that start with `release:` (stdout, then stderr) and the exit code; the Standard's steps (`release: standard: …`) are
new in rb-release and left out. The ruff-error and secret cases are the passing fixture plus one file written here, so
the fake token is never committed.
"""

from __future__ import annotations

import os
import random
import shutil
import string
import subprocess
import sys
from pathlib import Path

import pytest

GATE = Path(__file__).resolve().parents[2]
FIXTURES = GATE / "tests" / "data" / "parity"
TEMPLATE_GATE = "v1.20.10:template/scripts/release.py"  # the template's copy of the gate, read from git
RB_RELEASE = (sys.executable, "-c", "from rb_release.cli import main; main()", "check")
TEMPLATE = (sys.executable, "scripts/release.py", "--check")
IGNORED = "scripts/\n.venv/\n__pycache__/\n"  # the copied gate is not part of the project the gate checks


def _github_token() -> str:
    """A GitHub personal access token that is made up: built at test time, never written in the repo."""
    alphabet = string.ascii_letters + string.digits
    return "ghp_" + "".join(random.Random(7).choices(alphabet, k=36))  # noqa: S311


def _project(tmp_path: Path, name: str, fixture: str, extra_files: dict[str, str]) -> Path:
    root = tmp_path / name
    shutil.copytree(FIXTURES / fixture, root)
    (root / ".gitignore").write_text(IGNORED)
    for path, text in extra_files.items():
        (root / path).write_text(text)
    for args in (("init", "-q", "-b", "main"), ("add", "-A"), ("commit", "-qm", "init")):
        subprocess.run(  # noqa: S603
            ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],  # noqa: S607
            cwd=root,
            capture_output=True,
            check=True,
        )
    return root


def _run(command: tuple[str, ...], root: Path) -> tuple[list[str], int]:
    tools = str(Path(sys.executable).parent)  # this repo's ruff, ty, pytest
    env = {**os.environ, "PATH": f"{tools}{os.pathsep}{os.environ['PATH']}"}
    result = subprocess.run(command, cwd=root, env=env, text=True, capture_output=True, check=False)  # noqa: S603
    output = (result.stdout + result.stderr).splitlines()
    lines = [line for line in output if line.startswith("release:") and not line.startswith("release: standard: ")]
    return lines, result.returncode


def _both(tmp_path: Path, fixture: str, extra_files: dict[str, str]) -> tuple[tuple[list[str], int], ...]:
    template = _project(tmp_path, "template", fixture, extra_files)
    (template / "scripts").mkdir()
    copy = subprocess.run(["git", "show", TEMPLATE_GATE], cwd=GATE, capture_output=True, check=True).stdout  # noqa: S603, S607
    (template / "scripts" / "release.py").write_bytes(copy)
    command = _project(tmp_path, "command", fixture, extra_files)
    return _run(TEMPLATE, template), _run(RB_RELEASE, command)


def _requires(tool: str) -> pytest.MarkDecorator:
    return pytest.mark.skipif(shutil.which(tool) is None, reason=f"{tool} not installed")


def test_a_passing_project_gives_the_same_lines_and_exit_0(tmp_path: Path) -> None:
    template, command = _both(tmp_path, "passing", {})

    assert command == template
    lines, code = command
    assert lines[-1] == "release: gate passed"
    assert code == 0


def test_a_ruff_error_stops_both_at_the_same_step_with_exit_1(tmp_path: Path) -> None:
    template, command = _both(tmp_path, "passing", {"src/demo/__init__.py": "import os\n"})

    assert command == template
    lines, code = command
    assert "release: ruff check ... FAILED" in lines
    assert "release: ruff format --check ... ok" not in lines
    assert lines[-1] == "release: code failed"
    assert code == 1


@_requires("gitleaks")
def test_a_committed_token_stops_both_at_the_secret_scan_and_is_not_printed(tmp_path: Path) -> None:
    token = _github_token()
    template, command = _both(tmp_path, "passing", {"settings.py": f'GITHUB_TOKEN = "{token}"\n'})

    assert command == template
    lines, code = command
    assert lines[0] == "release: secret scan ... FAILED"
    assert lines[-1] == "release: code failed"
    assert token not in "\n".join(lines)
    assert code == 1


@pytest.mark.network
@_requires("osv-scanner")
def test_a_vulnerable_lock_file_ends_both_with_audit_failed_and_exit_3(tmp_path: Path) -> None:
    template, command = _both(tmp_path, "vulnerable", {})

    assert command == template
    lines, code = command
    assert "release: vulnerability audit ... FAILED" in lines
    assert lines[-1] == "release: audit failed"
    assert code == 3
