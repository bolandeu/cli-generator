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
   and the exit-code table from `conventions.md`.

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

10. **Version compatibility declared.**
    Fail if a project consuming this CLI has no way to declare
    `min_version`. Add `[cli] min_version` to the project config model.

11. **Bundled agent skill.**
    Fail if there's no `src/<package_name>/data/SKILL.md` (bundled as
    package data, not just sitting in the source repo) describing
    discovery, installation, init, auth, safety and error-inspection for
    an agent driving this CLI. Add it last, once the command surface it
    describes is stable.

## Reporting the audit

Before changing code, summarize findings as a short pass/fail list against
these eleven items — this tells the user (and you) exactly how much work
the refactor is and in what order, before any file gets touched.
