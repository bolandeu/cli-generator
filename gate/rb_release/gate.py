"""The release gate (`rb-release check`), run against any package.

Gate steps, in order — the first failure stops everything and prints that
step's name and output, then `release: code failed` (exit 1) or, when only
the vulnerability audit failed, `release: audit failed` (exit 3):

    secret scan (gitleaks over the git history; skipped with a notice when
    gitleaks isn't installed) · uv lock --check · ruff check ·
    ruff format --check · ty check · pytest ·
    contracts (tests/test_contracts.py: the consumers' cases from
    tests/contracts/<consumer>/*.yaml, run apart from pytest — a failing case
    stops the release and is named with its consumer) ·
    existing tests (never fails: lists every test that existed at the last tag
    and has since changed or gone — a changed or removed test function, changed
    module-level code of a test file, a changed snapshot or data file; each goes
    into the release report with its reason, the review rejects it without one) ·
    install section ([tool.rb.install] exists and is valid: homeserver a list
    of user names, mac a bool, extras an optional list of strings, no other key) ·
    external dependencies (every program src/ runs is declared in
    [[tool.rb.external]] and vice versa) ·
    build the wheel and install
    it into a throwaway venv with exactly the uv.lock dependency set (`uv sync
    --frozen`, then the wheel with --no-deps, then `uv pip check` — never
    resolving from an index, and every dependency [tool.uv.sources] takes from
    an explicit index must be installed as locked from there, so our
    packages can't be swapped for a same-named PyPI package),
    `<cli> --version` must print the version being
    built, `<cli> --help` must work (a library without a console script:
    every top-level package imports and importlib.metadata reports that
    version) · osv-scanner over uv.lock (skipped with a
    notice when osv-scanner isn't installed)

Settings in the package's pyproject.toml `[tool.cli-generator]`:
`gate_extras = ["x"]` runs ruff/ty/pytest with those extras installed.
"""

from __future__ import annotations

import ast
import os
import re
import shutil
import subprocess
import tempfile
import tomllib
import zipfile
from collections.abc import Callable
from pathlib import Path

CONTRACT_TESTS = "tests/test_contracts.py"
COMMANDS = (
    ("uv lock --check", ("uv", "lock", "--check")),
    ("ruff check", ("uv", "run", "ruff", "check", ".")),
    ("ruff format --check", ("uv", "run", "ruff", "format", "--check", ".")),
    ("ty check", ("uv", "run", "ty", "check")),
    ("pytest", ("uv", "run", "pytest", f"--ignore={CONTRACT_TESTS}")),  # contracts: their own step
)
AUDIT_STEP = "vulnerability audit"
EXIT_PASSED = 0
EXIT_CODE_FAILED = 1  # any code/packaging step: lock, lint, types, tests, wheel
EXIT_AUDIT_FAILED = 3  # only the osv-scanner audit: the code is fine, a dependency has a known vulnerability
TAG_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")

Echo = Callable[..., None]  # typer.echo: (message, nl=True, err=False)


class NotAPackage(Exception):
    """The gate was pointed at a directory without pyproject.toml: a usage error."""


class StepFailed(Exception):
    def __init__(self, output: str) -> None:
        super().__init__(output)
        self.output = output


# --- what a step reads from its input alone ---------------------------------------


_PROCESS_CALLS = {"run", "Popen", "check_output", "check_call", "call"}


def external_programs(source: str) -> set[str]:
    """Programs a module runs or looks up by a literal name.

    `require_cli("x", ...)`, `shutil.which("x")`, and `subprocess.run(["x", ...])`
    (also Popen/check_output/check_call/call). A name built at runtime isn't
    seen — call `require_cli` with the literal name first, then run its path.
    """
    found: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        func = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
        first = node.args[0]
        if func in ("require_cli", "which") and isinstance(first, ast.Constant) and isinstance(first.value, str):
            found.add(first.value)
        elif func in _PROCESS_CALLS and isinstance(first, ast.List | ast.Tuple) and first.elts:
            head = first.elts[0]
            if isinstance(head, ast.Constant) and isinstance(head.value, str):
                found.add(head.value)
    return found


def _top_level(source: str) -> tuple[dict[str, str], list[str]]:
    """A test module's top-level functions and classes by name, and its other statements (imports aside)."""
    defs: dict[str, str] = {}
    rest: list[str] = []
    for node in ast.parse(source).body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            defs[node.name] = ast.dump(node)  # no line numbers: a moved test is not a changed one
        elif not isinstance(node, ast.Import | ast.ImportFrom):
            rest.append(ast.dump(node))
    return defs, rest


def changed_existing_tests(path: str, old: str, new: str | None) -> list[str]:
    """What of `path` as it was (`old`) is changed or gone in `new` (None: the file is deleted). New tests don't count."""
    if new is None:
        return [f"{path} removed"]
    if old == new:
        return []
    if not path.endswith(".py"):  # a snapshot, test data: the file as a whole
        return [f"{path} changed"]
    try:
        old_defs, old_rest = _top_level(old)
        new_defs, new_rest = _top_level(new)
    except SyntaxError:
        return [f"{path} changed"]
    found = [f"{path}: module-level code changed"] if any(stmt not in new_rest for stmt in old_rest) else []
    for name in sorted(old_defs):
        if name not in new_defs:
            found.append(f"{path}::{name} removed")
        elif new_defs[name] != old_defs[name]:
            found.append(f"{path}::{name} changed")
    return found


_CONTRACT_RESULT = re.compile(r"::test_contract\[([^\]]+)\] (PASSED|FAILED|SKIPPED|ERROR)")


def contract_summary(output: str) -> str:
    """'N cases from K consumers' (+ failed / skipped) from a `pytest -vv` run of tests/test_contracts.py."""
    results = {case: status for case, status in _CONTRACT_RESULT.findall(output)}
    if not results:
        return "0 cases"
    consumers = {case.split(":", 1)[0] for case in results}
    cases, sources = len(results), len(consumers)
    summary = f"{cases} case{'s' * (cases != 1)} from {sources} consumer{'s' * (sources != 1)}"
    failed = sum(status in ("FAILED", "ERROR") for status in results.values())
    skipped = sum(status == "SKIPPED" for status in results.values())
    notes = [f"{failed} failed"] * bool(failed) + [f"{skipped} skipped (provider version)"] * bool(skipped)
    return f"{summary}: {', '.join(notes)}" if notes else summary


def _wheel_version(wheel: Path) -> str:
    """`Version:` from the wheel's METADATA — what importlib.metadata (and so `--version`) reports.

    Not the file name: it normalizes the local part (`+0814724` -> `+814724`).
    """
    with zipfile.ZipFile(wheel) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".dist-info/METADATA"))
        metadata = archive.read(name).decode()
    return next(line.split(":", 1)[1].strip() for line in metadata.splitlines() if line.startswith("Version:"))


def _normalized(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


# The defaults of copier.yml's `install_homeserver_users` and `install_mac`.
INSTALL_DEFAULT = """[tool.rb.install]
homeserver = ["rbtools"]
mac = true"""
INSTALL_KEYS = ("homeserver", "mac", "extras")


# --- the gate over one package ----------------------------------------------------


class Gate:
    """The gate steps over the package at `root`: the directory with its pyproject.toml."""

    def __init__(self, root: Path) -> None:
        self.root = root

    @classmethod
    def at(cls, root: Path) -> Gate:
        """The gate of the package at `root`; a directory without pyproject.toml is a usage error."""
        if not (root / "pyproject.toml").is_file():
            raise NotAPackage(
                f"No pyproject.toml in '{root}': run 'rb-release check' in the root directory of a package."
            )
        return cls(root)

    def _pyproject(self) -> dict:
        return tomllib.loads((self.root / "pyproject.toml").read_text())

    def _tool(self, name: str) -> dict:
        return self._pyproject().get("tool", {}).get(name, {})

    def gate_extras(self) -> list[str]:
        """`[tool.cli-generator] gate_extras`: optional-dependency extras the gate installs, so their tests run."""
        return list(self._tool("cli-generator").get("gate_extras", []))

    def _extra_args(self) -> list[str]:
        return [arg for extra in self.gate_extras() for arg in ("--extra", extra)]

    def git_output(self, *args: str) -> str:
        result = subprocess.run(args, cwd=self.root, check=True, text=True, capture_output=True)
        return result.stdout.strip()

    def step_output(self, *args: str, env: dict[str, str] | None = None) -> str:
        """Run one gate command; raise StepFailed with its combined output if it fails."""
        result = subprocess.run(args, cwd=self.root, text=True, capture_output=True, env=env, check=False)
        output = (result.stdout + result.stderr).strip()
        if result.returncode:
            raise StepFailed(f"$ {' '.join(args)}\n{output}")
        return output

    def tags(self) -> list[tuple[int, int, int]]:
        result = subprocess.run(
            ["git", "tag", "--list", "v*"], cwd=self.root, text=True, capture_output=True, check=False
        )
        listed = result.stdout.split()  # not a git repo yet (fresh scaffold): no tags
        return sorted((int(m[1]), int(m[2]), int(m[3])) for t in listed if (m := TAG_RE.match(t)))

    # --- gate steps ------------------------------------------------------------

    def run_command(self, argv: tuple[str, ...]) -> str:
        if argv[:2] == ("uv", "run"):  # run lint/types/tests with the configured extras installed
            argv = ("uv", "run", *self._extra_args(), *argv[2:])
        self.step_output(*argv)
        return ""

    def _changed_since(self, tag: str) -> list[str]:
        """Files that differ from `tag`: committed, staged, unstaged and untracked."""
        tracked = self.git_output("git", "diff", "--name-only", tag).splitlines()
        untracked = self.git_output("git", "ls-files", "--others", "--exclude-standard").splitlines()
        return sorted(set(tracked + untracked))

    def check_external_deps(self) -> str:
        """Every external program used in src/ is declared in [[tool.rb.external]], and every declared one is used."""
        entries = self._tool("rb").get("external", [])
        problems = [
            f"entry #{i + 1} needs `name` and `why`"
            for i, e in enumerate(entries)
            if not (e.get("name") and e.get("why"))
        ]
        declared = {entry.get("name") for entry in entries}
        used: dict[str, list[str]] = {}
        for path in sorted((self.root / "src").rglob("*.py")):
            for name in external_programs(path.read_text()):
                used.setdefault(name, []).append(str(path.relative_to(self.root)))
        problems += [
            f"`{name}` is run in {', '.join(files)} but not declared"
            for name, files in used.items()
            if name not in declared
        ]
        # detect = false: run in a way this scan can't see (an injected runner, an
        # absolute path) — declared on trust, but still with a `why`.
        hidden = {entry.get("name") for entry in entries if entry.get("detect", True) is False}
        unseen = sorted(declared - used.keys() - hidden)
        problems += [
            f"`{name}` is declared but nothing in src/ runs it (set detect = false if it's run in a way the gate "
            "can't see, e.g. an injected runner or an absolute path)"
            for name in unseen
        ]
        if problems:
            raise StepFailed(
                "pyproject.toml [[tool.rb.external]] doesn't match the code (standard §12):\n  - "
                + "\n  - ".join(problems)
                + '\nDeclare: [[tool.rb.external]] name = "x", required = true, min_version = "1.0", check = "x --version", why = "..."'
            )
        if not declared:
            return "none used, none declared"
        return f"{len(declared)} declared, all used" + (f" ({len(hidden)} with detect = false)" if hidden else "")

    def check_install_section(self) -> str:
        """`[tool.rb.install]` exists and is valid: no package is released without an install declaration."""
        install = self._tool("rb").get("install")
        if install is None:
            raise StepFailed(f"pyproject.toml has no [tool.rb.install]; add:\n{INSTALL_DEFAULT}")
        if not isinstance(install, dict):
            raise StepFailed(f"pyproject.toml [tool.rb.install] must be a table, not {type(install).__name__}")
        users, mac, extras = install.get("homeserver"), install.get("mac"), install.get("extras", [])
        problems = [
            f"`{key}` is unknown (allowed: {', '.join(INSTALL_KEYS)})" for key in install if key not in INSTALL_KEYS
        ]
        if not (isinstance(users, list) and all(isinstance(user, str) and user for user in users)):
            problems.append("`homeserver` must be a list of user names (non-empty strings, may be empty)")
        if not isinstance(mac, bool):
            problems.append("`mac` must be a bool (true or false)")
        if not (isinstance(extras, list) and all(isinstance(extra, str) for extra in extras)):
            problems.append("`extras` must be a list of strings")
        if problems:
            raise StepFailed(f"pyproject.toml [tool.rb.install]: {problems[0]}")
        return f"homeserver = {users}, mac = {str(mac).lower()}" + (f", extras = {extras}" if extras else "")

    def check_existing_tests(self) -> str:
        """Tests the last release had that are changed or gone now: a test is not edited to fit the code.

        Never fails — a requirement can change. The list goes into the release
        report, each entry with its reason (TDD).
        """
        versions = self.tags()
        if not versions:
            return "no release tag yet"
        last = "v{}.{}.{}".format(*versions[-1])
        found: list[str] = []
        for path in self._changed_since(last):
            if not path.startswith("tests/"):
                continue
            old = subprocess.run(["git", "show", f"{last}:{path}"], cwd=self.root, capture_output=True, check=False)
            if old.returncode:  # added since the tag
                continue
            current = self.root / path
            new = current.read_text(errors="replace") if current.is_file() else None
            found += changed_existing_tests(path, old.stdout.decode(errors="replace"), new)
        if not found:
            return f"none changed since {last}"
        listed = "\n  ".join(found)
        return f"{len(found)} changed since {last} — put each in the release report with its reason:\n  {listed}"

    def check_contracts(self) -> str:
        """The consumers' contract cases, as their own gate step: any failure stops the release."""
        if not (self.root / CONTRACT_TESTS).is_file():
            return f"none ({CONTRACT_TESTS} doesn't exist)"
        argv = ["uv", "run", *self._extra_args(), "pytest", CONTRACT_TESTS]
        argv += ["-vv", "--no-cov", "-p", "no:cacheprovider", "-rfE", "--tb=no"]  # -vv: the reason is not cut off
        result = subprocess.run(argv, cwd=self.root, text=True, capture_output=True, check=False)
        output = (result.stdout + result.stderr).strip()
        summary = contract_summary(output)
        if result.returncode not in (0, 5):  # 5: no case collected
            failures = [line for line in output.splitlines() if line.startswith(("FAILED", "ERROR"))]
            raise StepFailed(f"{summary}\n" + "\n".join(failures or [output]))
        return summary

    def check_secrets(self) -> str:
        """No key, token or password anywhere in the git history (gitleaks; `--redact`: the value is never printed)."""
        scanner = shutil.which("gitleaks")
        if scanner is None:
            return "skipped: gitleaks not installed (brew install gitleaks)"
        self.step_output(scanner, "git", "--redact", "--verbose", "--no-banner", "--no-color", str(self.root))
        return "no secrets in the git history"

    def check_vulnerabilities(self) -> str:
        scanner = shutil.which("osv-scanner")
        if scanner is None:
            return "skipped: osv-scanner not installed (brew install osv-scanner)"
        self.step_output(scanner, "--lockfile=uv.lock")
        return "no known vulnerabilities in uv.lock"

    def _check_library(self, python: Path, wheel: Path, dist: str, built: str) -> str:
        """No console script (a library): import every top-level package, compare importlib.metadata's version."""
        with zipfile.ZipFile(wheel) as archive:
            tops = sorted(
                {
                    name.split("/")[0].removesuffix(".py")
                    for name in archive.namelist()
                    if not name.split("/")[0].endswith((".dist-info", ".data"))
                    and (name.endswith(".py") or "/" in name)
                }
            )
        code = (
            "import importlib, importlib.metadata as m\n"
            f"for name in {tops!r}: importlib.import_module(name)\n"
            f"print(m.version({dist!r}))"
        )
        reported = self.step_output(str(python), "-c", code).splitlines()[-1].strip()
        if reported != built:
            raise StepFailed(f"importlib.metadata.version({dist!r}) is {reported!r}, but the wheel is version {built}")
        return f"{wheel.name}; imports {', '.join(tops)}; importlib.metadata version = {reported}"

    def check_index_sources(self, python: Path) -> None:
        """Every dependency [tool.uv.sources] takes from an explicit index is installed as uv.lock locked it from there."""
        uv = self._tool("uv")
        explicit = {index["name"] for index in uv.get("index", []) if index.get("explicit")}
        pinned = {
            _normalized(name): source["index"]
            for name, source in uv.get("sources", {}).items()
            if isinstance(source, dict) and source.get("index") in explicit
        }
        if not pinned:
            return
        lock = tomllib.loads((self.root / "uv.lock").read_text())
        locked = {package["name"]: package["version"] for package in lock["package"] if package["name"] in pinned}
        code = (
            "import importlib.metadata as m\n"
            f"for name in {sorted(pinned)!r}:\n"
            "    try: print(name, m.version(name))\n"
            "    except m.PackageNotFoundError: pass"  # not in the installed set (an extra): nothing to check
        )
        installed = dict(line.split() for line in self.step_output(str(python), "-c", code).splitlines())
        wrong = [
            f"{name} {version} (uv.lock: {locked.get(name)} from `{pinned[name]}`)"
            for name, version in sorted(installed.items())
            if version != locked.get(name)
        ]
        if wrong:
            raise StepFailed(f"installed from a package index other than their explicit index: {', '.join(wrong)}")

    def install_locked(self, python: Path) -> None:
        """Install exactly uv.lock's dependency set into the venv of `python`, each package from its locked source.

        Never `uv pip install <wheel>` or an exported requirements file: neither
        carries [tool.uv.sources], so our packages (rb-x from the explicit Gitea
        index) would be resolved from PyPI — where an unrelated package of the
        same name may live (dependency confusion).
        """
        env = {**os.environ, "UV_PROJECT_ENVIRONMENT": str(python.parent.parent)}
        self.step_output("uv", "sync", "--frozen", "--no-dev", "--no-install-project", "--quiet", env=env)
        self.check_index_sources(python)

    def check_installed_wheel(self) -> str:
        """Build the wheel, install it into a throwaway venv, run the CLI."""
        project = self._pyproject()["project"]
        script = next(iter(project.get("scripts", {})), None)
        with tempfile.TemporaryDirectory() as tmp:
            dist, venv = Path(tmp) / "dist", Path(tmp) / "venv"
            self.step_output("uv", "build", "--wheel", "--out-dir", str(dist))
            wheel = next(dist.glob("*.whl"))
            built = _wheel_version(wheel)
            if self.tags() and built.startswith("0.0.0"):
                raise StepFailed(f"built version {built}: the build saw no v* tag (uv-dynamic-versioning fell back)")
            self.step_output("uv", "venv", "--quiet", str(venv))
            python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            # The locked set, then the wheel without resolving anything, then
            # check the wheel's requirements are met by what's installed.
            self.install_locked(python)
            self.step_output("uv", "pip", "install", "--quiet", "--no-deps", "--python", str(python), str(wheel))
            self.step_output("uv", "pip", "check", "--python", str(python))
            if script is None:
                return self._check_library(python, wheel, project["name"], built)
            exe = python.parent / (f"{script}.exe" if os.name == "nt" else script)
            printed = self.step_output(str(exe), "--version").splitlines()
            reported = printed[-1].strip() if printed else ""
            if reported != built:
                raise StepFailed(f"`{script} --version` printed {reported!r}, but the wheel is version {built}")
            self.step_output(str(exe), "--help")
            return f"{wheel.name}; `{script} --version` = {reported}; `{script} --help` ok"

    def steps(self) -> list[tuple[str, Callable[[], str]]]:
        return [
            ("secret scan", self.check_secrets),
            *((name, lambda argv=argv: self.run_command(argv)) for name, argv in COMMANDS),
            ("contracts", self.check_contracts),
            ("existing tests", self.check_existing_tests),
            ("install section", self.check_install_section),
            ("external dependencies", self.check_external_deps),
            ("build + install wheel", self.check_installed_wheel),
            (AUDIT_STEP, self.check_vulnerabilities),
        ]

    def run_steps(self, echo: Echo) -> int:
        """Run every step, one `release: <step> ...` line each; the exit code: 0 passed, 1 code failed, 3 audit failed."""
        for name, step in self.steps():
            echo(f"release: {name} ... ", nl=False)
            try:
                detail = step()
            except StepFailed as exc:
                echo("FAILED")
                echo(f"\nrelease: gate step '{name}' failed:\n{exc.output}", err=True)
                # Last line + exit code tell whoever runs the gate (an agent, CI) whether
                # the code is broken or only a dependency needs a security bump.
                audit = name == AUDIT_STEP
                echo(f"release: {'audit' if audit else 'code'} failed", err=True)
                return EXIT_AUDIT_FAILED if audit else EXIT_CODE_FAILED
            echo(f"ok ({detail})" if detail else "ok")
        echo("release: gate passed")
        return EXIT_PASSED
