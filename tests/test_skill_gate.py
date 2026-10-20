"""SKILL.md and README.md name the gate as the uvx command at the template tag (ADR 0013), never the old forms."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = (ROOT / "skills" / "cli-builder" / "SKILL.md").read_text()
README = (ROOT / "README.md").read_text()

GATE = (
    'uvx --from "git+https://homeserver.tailee01ab.ts.net:3000/bolandeu/cli-generator.git'
    '@<template tag>#subdirectory=gate" rb-release check'
)
FORBIDDEN = ["rb-cli-core", "adopt_core", "uv run rb-release", "release.py --check"]


def section(text: str, start: str, end: str) -> str:
    """The text from the line starting with `start` up to the line starting with `end`."""
    match = re.search(rf"^{re.escape(start)}.*?(?=^{re.escape(end)}|\Z)", text, re.S | re.M)
    assert match, f"no section {start!r}"
    return match.group(0)


def test_docs_do_not_name_the_old_gate():
    for name, text in (("SKILL.md", SKILL), ("README.md", README)):
        found = [word for word in FORBIDDEN if word in text]
        assert not found, f"{name} names {found}"


def test_new_package_runs_the_gate_through_uvx():
    scaffold = section(SKILL, "## Mode: Scaffold", "## Mode: Refactor")
    assert GATE in scaffold


def test_update_has_one_step_switching_to_uvx_gate():
    update = section(SKILL, "## Mode: Update", "### Renaming the distribution")
    step = section(update, "14. **Switching to the gate through uvx**", "### ")
    assert GATE in step
    assert "scripts/release.py" in step and "uv lock" in step
    assert ".agents/antagor/antagor.toml" in step and "release: gate passed" in step
    assert len(re.findall(r"^\d+\. \*\*Switching", update, re.M)) == 1
