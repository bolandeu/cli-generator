# Refactor checklist

Work top to bottom. Each item assumes the ones above it are already done —
don't jump ahead (e.g. splitting out `--json` output is much harder before
commands are separated from business logic).

For each item: check the current repo, note pass/fail, fix failures in
order before moving to the next item.

1. **`src/` layout + `pyproject.toml` with `[project.scripts]`.**
   Fail if it's a loose script, a flat module, or installed via
   `python foo.py` instead of an installed console command.

2. **Commands contain no business logic.**
   Fail if a command function does real work inline instead of calling into
   a `core`/service layer. Extract into `core/services.py` before touching
   anything else — every later step assumes this split exists.

3. **Config/state/secrets are three separate things.**
   Fail if secrets are hardcoded, in a committed `.env`, or mixed into the
   same file as project config. Move secrets to `credentials/manager.py`
   (keyring + env var fallback, see the template's copy). This is a
   security fix — call it out explicitly to the user even if they didn't
   ask for one.

4. **Dual output (human + `--json`).**
   Fail if the only output is `print()`/decorated terminal text with no
   machine-readable mode. Add the `output/` module (human.py + json.py) and
   route every command through `emit_success`/`emit_error`.

5. **Structured errors + fixed exit codes.**
   Fail if failures are bare `sys.exit(1)`, uncaught exceptions as the
   user-facing failure, or ad-hoc messages. Introduce `CliError` subclasses
   and the exit-code table from `conventions.md`, wrap every command in
   `@output.guard` (unmapped exceptions → `UNEXPECTED` envelope), send
   human errors to stderr, and make a bare `<cli>` / `<cli> <group>` print
   help with exit 0 (`output.group`), not a "Missing command" error.
   External calls go through a `providers.HttpProvider` subclass so
   network/HTTP failures come out as `PROVIDER_ERROR` / `AUTH_REQUIRED`
   instead of a `requests` traceback. Every provider (a `providers.Provider`
   subclass) implements `health_check()`, and a CLI with credentials has
   `auth status [--check] --json` in the exact shape of
   `architecture.md` §4 — copy `credentials/health.py`, the command and
   the shape test from the template; fail on any other status command
   format, on a status that prints values, or on placeholder credentials
   stored just to make it green.

6. **`doctor` command exists.**
   Fail if there's no single command that checks environment/config/auth
   readiness and reports it structurally.

7. **`--non-interactive` on every prompting command.**
   Fail if `init`/`auth login`/etc. always prompt with no flag to disable
   it — this blocks any agent/CI use.

8. **Destructive commands are gated.**
   Fail if any command that deletes, overwrites a remote resource, or
   otherwise changes external state irreversibly can run without a
   `--dry-run` preview available and without `--confirm` required under
   `--non-interactive`. An agent must never be able to trigger this by
   accident just by always passing `--non-interactive`. Use
   `output.is_dry_run`/`output.require_confirmation`; list the affected
   commands explicitly in the bundled SKILL.md's Safety section.

9. **Cross-platform correctness.**
   Fail on `os.system`, `shell=True`, hardcoded `/`-style paths, or reliance
   on a specific shell's builtins. Replace with `pathlib`/`shutil`; use
   `platformdirs` for user-level config location.

10. **Version compatibility declared — and enforced; releases per the
    standard.**
    Fail if a project consuming this CLI has no way to declare
    `min_version`, or declares it but nothing checks it — add `[cli]
    min_version` to the project config model and `services.check_cli_compat`
    to `load_config`. Also fail on any of these (`architecture.md` §8):
    a `version =` line in `pyproject.toml` or a hard-coded version string
    (→ tag the current version first if untagged, `git tag -a vX.Y.Z -m
    vX.Y.Z <sha>`, then `dynamic = ["version"]` + uv-dynamic-versioning +
    `[tool.uv] cache-keys`, runtime via `importlib.metadata`); a
    hand-edited `CHANGELOG.md` / `## [Unreleased]` section (→ towncrier
    config, the start marker above the newest release, unreleased entries
    moved into `changelog.d/` fragments — except for a package that has
    **never been released** (no `v*` tag): when it gets its first tag
    `vX.Y.Z`, rename `## [Unreleased]` to `## [X.Y.Z] - <date>` instead,
    since those changes ship in that tag); a `scripts/release.py` that
    isn't the template's verbatim copy; a dependency on another of our
    tools by `branch =`, bare git URL or committed `path =` (→ `tag =` pin
    + compatible range); a subprocess call to another of our CLIs without
    a `core.deps.require_cli(...)` minimum-version check.

11. **Bundled agent skill + quality gates.**
    Fail if there's no `src/<package_name>/data/SKILL.md` (bundled as
    package data, not just sitting in the source repo) with the
    conventions an agent needs — install, `--json`, exit codes,
    credentials, dry-run/confirm — and *no* command list (commands come
    from docstrings via a bare `<cli>`; fail if any docstring is missing
    or stale). Fail too if the --help contract isn't enforced
    (`architecture.md` §5): no `tests/test_help.py` + `tests/snapshots/help/`
    (copy the test, then `uv run pytest --snapshot-update` and read every
    generated page — it's usually the first time anyone has), no
    `.claude/settings.json` hooks + `scripts/check_command_docstrings.py`,
    no versioned `.githooks/pre-commit`. Commands missing an `Example:`
    line or a parameter `help=` are fixed here, not waived. Also fail if `pyproject.toml` has no coverage
    `fail_under`, ruff doesn't select `S`, or CI has no dependency audit
    step — copy all three from the template, along with
    `scripts/release.py` (whose `--check` is the whole gate) and, if the
    repo keeps CI, its workflow (one `ubuntu-24.04` job running only
    `release.py --check`, lowest supported Python, current action
    majors) and `dependabot.yml` (monthly, one
    group per ecosystem).

12. **Installable from GitHub.**
    Fail if `uv tool install "git+<repo-url>"` doesn't produce a working
    command on a clean machine — no GitHub repo at all, no `[build-system]`
    in `pyproject.toml`, package data (the bundled SKILL.md) not shipped in
    the wheel, or README.md / `data/SKILL.md` still carrying an
    `<owner>/<repo>` placeholder instead of the real URL. Fix via
    SKILL.md's "Publish to GitHub" section (private repo by default; ask
    before creating anything). This is the item that makes the previous
    eleven usable from anywhere but the dev checkout.

## Reporting the audit

Before changing code, summarize findings as a short pass/fail list against
these twelve items — this tells the user (and you) exactly how much work
the refactor is and in what order, before any file gets touched.
