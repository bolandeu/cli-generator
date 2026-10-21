"""The workflow of this repo that runs the template gate on homeserver, read as data."""

import re
from pathlib import Path

import yaml

WORKFLOW = Path(__file__).resolve().parent.parent / ".gitea" / "workflows" / "template-gate.yml"

# Tags that exist upstream; some actions publish no floating major tag.
KNOWN_ACTION_TAGS = {"actions/checkout": {"v4"}}

ANTAGOR_PIN = re.compile(r"uv tool install .*antagor\.git@([0-9a-f]{40}|v\d+\.\d+\.\d+)\b")


def load():
    workflow = yaml.safe_load(WORKFLOW.read_text())
    workflow["triggers"] = workflow.pop(True, workflow.get("on"))  # YAML reads `on` as True
    return workflow


def steps():
    return load()["jobs"]["gate"]["steps"]


def test_runs_on_push_and_on_demand():
    triggers = load()["triggers"]
    assert {"push", "workflow_dispatch"} <= set(triggers)
    assert not (triggers["push"] or {}).get("branches"), "antagor/publish-<commit> branches must trigger it"


def test_job_uses_docker_runner_with_the_ci_cache_volume():
    job = load()["jobs"]["gate"]
    assert job["runs-on"] == "docker"
    assert job["container"]["image"] == "node:22-bookworm"
    assert "--init" in job["container"]["options"]
    assert "ci-cache:/cache" in job["container"]["volumes"]
    assert job["timeout-minutes"] == 60
    assert job["env"]["UV_PYTHON"] == "3.12"


def test_installs_the_tools_the_gate_needs():
    runs = "\n".join(step.get("run", "") for step in steps())
    assert "astral.sh/uv/install.sh" in runs
    assert "/usr/local/bin/gitleaks" in runs
    assert "/usr/local/bin/osv-scanner" in runs
    assert ANTAGOR_PIN.search(runs)


def test_template_gate_is_the_last_step():
    assert steps()[-1]["run"].strip() == "sh scripts/check_template.sh"


def test_every_action_tag_exists():
    used = [step["uses"] for step in steps() if "uses" in step]
    assert used
    for ref in used:
        action, tag = ref.split("@")
        assert tag in KNOWN_ACTION_TAGS.get(action, set()), ref
