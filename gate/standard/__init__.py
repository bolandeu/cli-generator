"""The Standard's mandatory rules, checked from outside: the gate's `standard: <step>` steps.

They run after the gate has built the wheel and installed it into a throwaway venv. A rule either probes the
installed console script (a library has none: those rules are skipped) or reads the package's files. A broken
rule raises Broken with what breaks it (the command, the file); the gate names the step and the section.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from collections.abc import Callable, Iterable, Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

# The Standard's table of exit codes (section Errors; in a template package: core/errors.py EXIT_CODES).
EXIT_CODES = frozenset(range(7))
UNKNOWN_OPTION = "--rb-release-unknown-option"
NO_SCRIPT = "skipped: no console script, a library"
DOCS = ("README.md", "AGENTS.md")
WORKFLOWS = ".gitea/workflows/"
GATE_COMMAND = "rb-release check"
# What a CI runner sets and Typer reads at import (forcing terminal output): the pytest step runs with them,
# every probe of the installed script runs without them.
CI_ENV = {"GITHUB_ACTIONS": "true", "FORCE_COLOR": "1", "PY_COLORS": "1"}

_PANEL_HEADING = re.compile(r"^╭─ .+ ─")  # Typer's rich panel
_PLAIN_HEADING = re.compile(r"^\S.*:$")  # Click's plain help
_COMMAND_NAME = re.compile(r"\w")
_JSON_OPTION = re.compile(r"(?<![\w-])--json(?![\w-])")


class Broken(Exception):
    """The package breaks a mandatory rule; the message names the command or the file."""


def _entries(lines: Iterator[str]) -> list[str]:
    """The first word of each entry of the section whose heading was just read; wrapped description lines are skipped."""
    names: list[str] = []
    indent = None
    for line in lines:
        body = line.rstrip().removeprefix("│").removesuffix("│")
        if not body.strip() or body.startswith("╰"):
            break
        depth = len(body) - len(body.lstrip())
        indent = depth if indent is None else indent
        if depth == indent:  # deeper: a wrapped description line
            names.append(body.split()[0])
    return names


def _sections(help_text: str) -> list[tuple[bool, list[str]]]:
    """Every section of a help text, titled in any language: (is it a Typer rich panel, its entry names)."""
    lines = help_text.splitlines()
    found: list[tuple[bool, list[str]]] = []
    for number, line in enumerate(lines):
        rich = bool(_PANEL_HEADING.match(line))
        indented = lines[number + 1 : number + 2] and lines[number + 1].startswith(" ")
        if rich or (_PLAIN_HEADING.match(line) and indented):
            found.append((rich, _entries(iter(lines[number + 1 :]))))
    return found


def listed_commands(help_text: str) -> list[str]:
    """The names a help text lists in its commands section: the one whose entries are names, not options.

    The heading's title does not matter (a package may translate it). A rich panel right before the options
    panel lists Typer's arguments, not commands.
    """
    sections = _sections(help_text)
    names: list[str] = []
    for (rich, section), (_, following) in zip(sections, [*sections[1:], (False, [])], strict=True):
        before_options = rich and following[:1] and following[0].startswith("-")
        if section and _COMMAND_NAME.match(section[0]) and not before_options:
            names += section
    return names


@dataclass(frozen=True)
class Run:
    """One run of the console script: its command line, exit code and stdout."""

    command: str
    code: int
    stdout: str

    def __str__(self) -> str:
        return f"`{self.command}`"


def probe_env() -> dict[str, str]:
    """The environment for a run of the installed script: the gate's own, without the CI variables."""
    return {name: value for name, value in os.environ.items() if name not in CI_ENV}


class Package:
    """The package at `root` and the console script the gate installed from its wheel (None: a library)."""

    def __init__(self, root: Path, script: Path | None) -> None:
        self.root = root
        self.script = script

    def run(self, *args: str) -> Run:
        assert self.script is not None  # noqa: S101 - Rule.verify skips the CLI rules of a library
        result = subprocess.run(  # noqa: S603 - the script the gate has just installed
            [str(self.script), *args],
            cwd=self.root,
            env=probe_env(),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        return Run(" ".join([self.script.name, *args]), result.returncode, result.stdout)

    def run_each(self, argvs: Iterable[tuple[str, ...]]) -> list[Run]:
        """Run the script once per argv, in parallel; the runs in the order of `argvs`."""
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as pool:
            return list(pool.map(lambda argv: self.run(*argv), argvs))

    @cached_property
    def bare(self) -> Run:
        return self.run()

    @cached_property
    def helps(self) -> dict[tuple[str, ...], Run]:
        """The `--help` run of every command and group the bare script lists, down through the groups."""
        found: dict[tuple[str, ...], Run] = {}
        level = [(name,) for name in listed_commands(self.bare.stdout)]
        while level:
            runs = self.run_each((*path, "--help") for path in level)
            found.update(zip(level, runs, strict=True))
            level = [
                (*path, name) for path, run in zip(level, runs, strict=True) for name in listed_commands(run.stdout)
            ]
        return found

    @cached_property
    def leaves(self) -> list[tuple[str, ...]]:
        """The commands that are not groups: their help lists no commands."""
        return [path for path, run in self.helps.items() if not listed_commands(run.stdout)]

    def command(self, path: tuple[str, ...]) -> str:
        assert self.script is not None  # noqa: S101 - Rule.verify skips the CLI rules of a library
        return f"`{' '.join([self.script.name, *path])}`"


def _in_table(run: Run) -> None:
    if run.code not in EXIT_CODES:
        raise Broken(
            f"{run} exits {run.code}: exit code {run.code} is not in the Standard's table "
            f"({min(EXIT_CODES)} to {max(EXIT_CODES)})"
        )


def _envelope(run: Run, name: str) -> dict:
    """stdout as the envelope: one JSON object, `ok` a bool; `ok: false` carries `error.code` and `error.message`."""
    try:
        payload = json.loads(run.stdout)
    except ValueError:
        payload = None
    if not isinstance(payload, dict) or not isinstance(payload.get("ok"), bool):
        raise Broken(f"{run} printed no {name} on stdout (a JSON object with `ok`): {run.stdout.strip()[:200]!r}")
    error = payload.get("error")
    fields = isinstance(error, dict) and all(isinstance(error.get(key), str) for key in ("code", "message"))
    if not payload["ok"] and not fields:
        raise Broken(f"{run} printed `ok: false` without `error.code` and `error.message` (the {name})")
    return payload


def check_commands(package: Package) -> str:
    bare = package.bare
    if bare.code:
        raise Broken(f"{bare} exits {bare.code}: with no arguments it lists the commands and exits 0")
    if not package.helps:
        raise Broken(f"{bare} lists no commands (no commands section in its output)")
    failing = [run for run in package.helps.values() if run.code]
    if failing:
        raise Broken(f"{failing[0]} exits {failing[0].code}: every command and group answers --help with exit 0")
    groups = len(package.helps) - len(package.leaves)
    return f"{len(package.leaves)} commands and {groups} groups answer --help"


def check_json(package: Package) -> str:
    if _JSON_OPTION.search(package.bare.stdout):
        return f"{len(package.leaves)} commands accept --json (the root lists it)"
    missing = [package.command(path) for path in package.leaves if not _JSON_OPTION.search(package.helps[path].stdout)]
    if missing:
        raise Broken(f"no --json in {', '.join(missing)}: every command accepts it (its --help or the root's lists it)")
    return f"{len(package.leaves)} commands accept --json"


def check_errors(package: Package) -> str:
    for run in package.run_each(("--json", *path, UNKNOWN_OPTION) for path in package.leaves):
        _in_table(run)
        if run.code != 2:
            raise Broken(f"{run} exits {run.code}: an unknown option is exit 2")
        if _envelope(run, "error envelope")["ok"]:
            raise Broken(f"{run} printed `ok: true`: the error envelope has `ok: false`")
    return f"an unknown option: exit 2 and the error envelope, in {len(package.leaves)} commands"


def check_health(package: Package) -> str:
    for path, report in ((("doctor",), None), (("auth", "status"), "credentials")):
        if path not in package.leaves:
            raise Broken(f"no {package.command(path)} command")
        run = package.run(*path, "--json")
        _in_table(run)
        payload = _envelope(run, "envelope")
        if report and not isinstance(payload.get(report), list):
            raise Broken(f"{run} printed no `{report}` list")
    return "doctor --json and auth status --json give the envelope"


def check_docs(package: Package) -> str:
    missing = [name for name in DOCS if not (package.root / name).is_file()]
    if missing:
        raise Broken(f"no {', '.join(missing)} in the package root")
    return ", ".join(DOCS)


def check_ci(package: Package) -> str:
    folder = package.root / WORKFLOWS
    workflows = sorted(path for path in folder.glob("*") if path.suffix in (".yml", ".yaml"))
    for path in workflows:
        if GATE_COMMAND in path.read_text(errors="replace"):
            return f"{path.relative_to(package.root)} runs {GATE_COMMAND}"
    raise Broken(f"no workflow under {WORKFLOWS} runs `{GATE_COMMAND}`")


@dataclass(frozen=True)
class Rule:
    """A mandatory rule: the gate's step `standard: <step>`, the Standard's section that states it, its check."""

    step: str
    section: str
    check: Callable[[Package], str]
    probes_cli: bool = True

    def verify(self, package: Package) -> str:
        """The step's detail line; raises Broken. A rule that probes the CLI is skipped for a library."""
        if self.probes_cli and package.script is None:
            return NO_SCRIPT
        return self.check(package)


RULES = (
    Rule("commands", "Commands", check_commands),
    Rule("json", "Output", check_json),
    Rule("errors", "Errors", check_errors),
    Rule("health", "Health", check_health),
    Rule("docs", "Docs", check_docs, probes_cli=False),
    Rule("ci", "CI", check_ci, probes_cli=False),
)
