"""The gate's `standard: <rule>` steps: `rb-release check` on a fixture CLI that meets every mandatory rule of the
Standard, and on copies of it that each break one rule (one change applied here)."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from conftest import PYPROJECT
from rb_release.cli import app

STANDARD_STEPS = ["commands", "json", "errors", "health", "docs", "ci"]
SCRIPT = """
[project.scripts]
demo = "demo:main"
"""
# A stdlib-only CLI: groups list their commands under `Commands:` (Click's plain help), leaf commands list
# their options, an unknown option is exit 2 and, with --json, the error envelope on stdout.
COMPLIANT = '''"""A demo CLI that meets the Standard's mandatory rules."""

import importlib.metadata
import json
import sys

COMMANDS = {
    "status": ("Show the status.", ["--json"]),
    "doctor": ("Run the diagnostic checks.", ["--json"]),
    "auth status": ("Report the credentials.", ["--json"]),
}
GROUPS = {"": "A demo CLI.", "auth": "Credentials."}
OUTPUT = {
    "status": {"ok": True},
    "doctor": {"ok": True, "checks": []},
    "auth status": {"ok": True, "credentials": []},
}
BARE_EXIT = 0
USAGE_EXIT = 2


def children(group: str) -> dict[str, str]:
    """The commands and groups right under `group`, with their one-line help."""
    entries = {**{name: about for name, (about, _) in COMMANDS.items()}, **GROUPS}
    depth = len(group.split()) + 1
    return {
        name.split()[-1]: about
        for name, about in entries.items()
        if name.startswith(group) and len(name.split()) == depth
    }


def group_help(group: str) -> str:
    rows = "\\n".join(f"  {name}  {about}" for name, about in children(group).items())
    return f"Usage: demo {group} COMMAND\\n\\n{GROUPS[group]}\\n\\nCommands:\\n{rows}\\n"


def error(message: str, as_json: bool) -> int:
    if as_json:
        error = {"code": "INVALID_ARGUMENTS", "message": message}
        print(json.dumps({"ok": False, "error": error}))
    else:
        print(f"Error: {message}", file=sys.stderr)
    return USAGE_EXIT


def run(argv: list[str]) -> int:
    path = " ".join(arg for arg in argv if not arg.startswith("-"))
    options = [arg for arg in argv if arg.startswith("-")]
    if "--version" in options:
        print(importlib.metadata.version("demo"))
        return 0
    if path in GROUPS:
        print(group_help(path))
        return 0 if options or path else BARE_EXIT
    if path not in COMMANDS:
        return error(f"No such command '{path}'.", "--json" in options)
    about, accepted = COMMANDS[path]
    unknown = [option for option in options if option not in [*accepted, "--help"]]
    if unknown:
        return error(f"No such option: {unknown[0]}", "--json" in options)
    if "--help" in options:
        rows = "\\n".join(f"  {option}" for option in [*accepted, "--help"])
        print(f"Usage: demo {path} [OPTIONS]\\n\\n{about}\\n\\nOptions:\\n{rows}")
        return 0
    print(json.dumps(OUTPUT[path]))
    return 0


def main() -> None:
    sys.exit(run(sys.argv[1:]))
'''


def _changed(old: str, new: str) -> str:
    """The compliant CLI with one change applied."""
    assert old in COMPLIANT, old
    return COMPLIANT.replace(old, new)


def _check(in_package, module: str = COMPLIANT, remove: str | None = None):
    root = in_package(module, pyproject=PYPROJECT + SCRIPT)
    if remove:
        (root / remove).unlink()
    return CliRunner().invoke(app, ["check"])


def _failed_at(result, step: str, section: str) -> str:
    """The failure output of a gate that stopped at `standard: <step>`, naming `section`."""
    assert result.stdout.splitlines()[-1] == f"release: standard: {step} ... FAILED", result.output
    assert f"release: gate step 'standard: {step}' failed:" in result.stderr
    assert f"Standard, section {section}:" in result.stderr, result.stderr
    assert result.stderr.strip().splitlines()[-1] == "release: code failed"
    assert result.exit_code == 1
    return result.stderr


def test_a_compliant_cli_passes_every_standard_step(in_package) -> None:
    result = _check(in_package)

    lines = result.stdout.splitlines()
    standard = [line for line in lines if line.startswith("release: standard: ")]
    assert [line.split(" ... ")[0] for line in standard] == [f"release: standard: {s}" for s in STANDARD_STEPS]
    assert all(line.split(" ... ")[1].startswith("ok") for line in standard), result.output
    assert lines[-1] == "release: gate passed"
    assert result.exit_code == 0


def test_a_bare_command_that_exits_2_fails_at_commands(in_package) -> None:
    result = _check(in_package, _changed("BARE_EXIT = 0", "BARE_EXIT = 2"))

    assert "`demo` exits 2" in _failed_at(result, "commands", "Commands")


def test_a_command_without_json_fails_at_json(in_package) -> None:
    module = _changed('"status": ("Show the status.", ["--json"])', '"status": ("Show the status.", [])')

    assert "`demo status`" in _failed_at(_check(in_package, module), "json", "Output")


def test_a_json_error_in_plain_text_fails_at_errors(in_package) -> None:
    module = _changed('print(json.dumps({"ok": False, "error": error}))', 'print(error["message"])')

    assert "error envelope" in _failed_at(_check(in_package, module), "errors", "Errors")


def test_an_exit_code_outside_the_table_fails_at_errors(in_package) -> None:
    result = _check(in_package, _changed("USAGE_EXIT = 2", "USAGE_EXIT = 7"))

    assert "exit code 7 is not in the Standard's table" in _failed_at(result, "errors", "Errors")


def test_a_cli_without_doctor_fails_at_health(in_package) -> None:
    result = _check(in_package, _changed('    "doctor": ("Run the diagnostic checks.", ["--json"]),\n', ""))

    assert "no `demo doctor` command" in _failed_at(result, "health", "Health")


def test_auth_status_without_credentials_fails_at_health(in_package) -> None:
    module = _changed('"auth status": {"ok": True, "credentials": []}', '"auth status": {"ok": True}')

    assert "`demo auth status --json`" in _failed_at(_check(in_package, module), "health", "Health")


@pytest.mark.parametrize("missing", ["README.md", "AGENTS.md"])
def test_a_package_without_its_docs_fails_at_docs(in_package, missing: str) -> None:
    assert missing in _failed_at(_check(in_package, remove=missing), "docs", "Docs")


def test_a_package_without_a_gitea_workflow_fails_at_ci(in_package) -> None:
    result = _check(in_package, remove=".gitea/workflows/ci.yml")

    assert ".gitea/workflows/" in _failed_at(result, "ci", "CI")


def test_a_library_without_a_console_script_skips_the_cli_rules(in_package) -> None:
    in_package('"""A demo library."""\n')

    result = CliRunner().invoke(app, ["check"])

    lines = {line.split(" ... ")[0]: line.split(" ... ")[1] for line in result.stdout.splitlines() if " ... " in line}
    for step in ("commands", "json", "errors", "health"):
        assert lines[f"release: standard: {step}"] == "ok (skipped: no console script, a library)"
    assert result.exit_code == 0
