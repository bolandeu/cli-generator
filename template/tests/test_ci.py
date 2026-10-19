"""The Gitea Actions workflow, when the project has one (include_ci=true)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".gitea" / "workflows" / "ci.yml"


def test_no_github_workflow() -> None:
    assert not (ROOT / ".github").exists()


def test_workflow_runs_the_gate_on_the_docker_runner() -> None:
    if not WORKFLOW.exists():
        pytest.skip("include_ci=false: no workflow")
    job = yaml.safe_load(WORKFLOW.read_text())["jobs"]["gate"]
    assert job["runs-on"] == "docker"
    assert "ci-cache:/cache" in job["container"]["volumes"]
    checkout = next(step for step in job["steps"] if str(step.get("uses", "")).startswith("actions/checkout@"))
    assert checkout["with"]["fetch-depth"] == 0
    assert job["steps"][-1]["run"] == "uv run scripts/release.py --check"


def _steps() -> list[dict]:
    return yaml.safe_load(WORKFLOW.read_text())["jobs"]["gate"]["steps"]


def test_scanners_are_installed_before_the_gate_at_pinned_versions() -> None:
    if not WORKFLOW.exists():
        pytest.skip("include_ci=false: no workflow")
    steps = _steps()
    gate = next(i for i, step in enumerate(steps) if step.get("run") == "uv run scripts/release.py --check")
    scripts = [step["run"] for step in steps[:gate] if "run" in step]
    for tool in ("osv-scanner", "gitleaks"):
        script = next(s for s in scripts if f"/cache/bin/{tool}-" in s)
        urls = re.findall(r"https://github\.com/\S+", script)
        assert urls
        assert all(re.search(r"/download/v\d+\.\d+\.\d+/", url) for url in urls)
        assert "latest" not in script


def test_scanners_are_cached_per_pinned_version() -> None:
    if not WORKFLOW.exists():
        pytest.skip("include_ci=false: no workflow")
    script = next(step["run"] for step in _steps() if "gitleaks" in step.get("run", ""))
    lines = script.splitlines()
    for tool, version in (("osv-scanner", "2.7.0"), ("gitleaks", "8.30.1")):
        cached = f"/cache/bin/{tool}-{version}"
        var = next(line.split("=")[0] for line in lines if line.endswith(f"={cached}"))
        download = next(line for line in lines if line.startswith(f"[ -x ${var} ] ||"))
        assert f"/download/v{version}/" in download
        assert f"ln -sf ${var} /usr/local/bin/{tool}" in lines
