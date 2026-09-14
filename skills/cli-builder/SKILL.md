---
name: cli-builder
description: Use when the task is to create a new CLI tool/package, or to refactor/audit an existing CLI or script onto a single shared architecture (Python + uv + Typer, project-local config, OS-keychain credentials, dual human/JSON output, AI-readable errors). Triggers on requests like "create a CLI for X", "build a command-line tool that...", "refactor this script into a proper CLI", "bring this package under our CLI architecture".
---

# CLI Builder

This skill produces every CLI tool under one architecture, so that a year from
now any of them can be opened by a coding agent and understood without
re-deriving conventions. It has two modes. Pick one before doing anything else.

- **Scaffold** — no working CLI exists yet, or the existing one is being fully
  replaced.
- **Refactor** — a CLI or script already exists and should be brought onto
  this architecture while preserving its behavior and history.

Read `reference/architecture.md` once per session before generating or
judging any code — it is the contract every generated package must satisfy.
`reference/conventions.md` has the exact JSON envelope, error codes and exit
codes to reuse verbatim (do not invent new ones per project).

Architecture governs the package's *shape*. The code you actually write
inside it (`core/services.py`, a `providers/` integration, a migrated
function) is governed by these four rules instead
(adapted from the MIT-licensed [karpathy-guidelines](https://github.com/multica-ai/andrej-karpathy-skills)):

1. **Think before coding.** State assumptions; if multiple interpretations
   exist, present them instead of picking silently; push back if the task
   implies more than it needs.
2. **Simplicity first.** Minimum code that solves the task — no commands,
   providers, or config fields beyond what was asked; no abstractions for
   single-use code; no error handling for scenarios that can't happen.
3. **Surgical changes** (Refactor mode especially). Touch only what the
   checklist item or request requires — don't reformat, "improve," or
   refactor adjacent code you weren't asked to touch.
4. **Goal-driven execution.** Turn the task into a verifiable check (a
   test that reproduces a bug, then passes) rather than looping on "make
   it work" — this is why every mode below ends in `uv sync && pytest &&
   doctor`.

## Mode: Scaffold

1. Clarify with the user (or infer from the task) before generating:
   - `package_name` — snake_case, importable, becomes the shell command name.
   - `project_name`, one-line `description`, `author_name`.
   - Whether it needs credentials (`include_auth`) — default yes if the task
     mentions any external API/provider.
   - `repository_url` — the GitHub URL this will be pushed to, if known
     (e.g. `https://github.com/you/mycli`). It's fine to leave blank and
     fill in later; it only pre-fills the "install from GitHub on any
     machine" instructions in README.md and the bundled SKILL.md.
   - What `run` should actually do — this is the one piece of real business
     logic the template does not provide.
2. Generate the skeleton with copier, pointing it at this plugin's repo
   root (its `copier.yml` has `_subdirectory: template`, so copier finds
   the actual template files under `template/` automatically — no
   `--subdirectory` flag needed):

   ```bash
   uvx copier copy /absolute/path/to/this/plugin/repo <dest-dir> \
     --data package_name=<name> --data project_name="<Name>" \
     --data description="<one line>" --data author_name="<name>" \
     --data include_auth=true
   ```

   Once this plugin's repo is on GitHub, `gh:<owner>/<repo>` also works as
   the template source in place of a local path.
3. Implement the real logic:
   - Business logic goes in `src/<package_name>/core/services.py` (or new
     modules under `core/`), never inside `commands/*.py`. Commands stay
     thin: parse args → call a service → call `output.emit_success` /
     `output.guard`.
   - External integrations (APIs, LLMs, etc.) go under `providers/`,
     implementing the `Provider` protocol.
   - Wire the real work into `commands/run.py`, replacing the placeholder.
4. Verify before calling it done:
   ```bash
   cd <dest-dir> && uv sync && uv run pytest && uv run <package_name> doctor
   ```
5. Do not `git init`/create a remote/push without the user's explicit
   go-ahead — scaffolding is local until they say otherwise.

## Mode: Refactor

Never rewrite blind. Work through `reference/refactor-checklist.md` in the
order it's written — later items assume earlier ones are already true (e.g.
you can't add `--json` output cleanly before commands are split from
business logic).

0. **Work on a branch, not on main.** This touches most files in the repo
   across several checklist items. Before changing anything: run `git
   status` (stash or ask about anything uncommitted first — never start a
   refactor on top of someone else's in-progress work), then create a
   feature branch (`git checkout -b cli-architecture-refactor` or similar)
   unless the user says otherwise or is already on one. This is what makes
   the refactor reviewable as one diff and trivially abandonable if it goes
   sideways — do not skip it even for a "quick" refactor.
1. **Audit first.** Read the existing package and check it against every
   item in the checklist. Report gaps before changing anything (a short
   list: what's missing, what's already fine — don't redo what's already
   compliant).
2. **Decide the migration strategy** based on the audit:
   - If the project already has significant structure worth keeping
     (its own tests, git history, real logic scattered through files):
     migrate in place, checklist item by item, smallest safe commits.
     Generate the reference skeleton into a scratch directory (same copier
     command as Scaffold mode, into a `/tmp` or scratchpad path) purely as a
     structural reference to copy specific files from (`core/errors.py`,
     `output/`, `credentials/manager.py` rarely need project-specific
     changes — copy them near-verbatim) — do not overwrite the target
     directory with it. `scripts/` (the docstring-drift hook) rarely needs
     project-specific changes either — copy it near-verbatim, then run
     `scripts/install_hooks.sh` once in the target repo.
   - If the existing code is a small/ad-hoc script with little worth
     preserving beyond its core logic: scaffold fresh (Scaffold mode) into
     a new directory, then port the actual logic into
     `core/services.py` and `providers/`.
3. Preserve behavior: whatever the script/CLI did before must still work
   after, just reachable through the new command surface and passing
   through `output.emit_success`/`output.guard` instead of raw prints.
4. Secrets found hardcoded, in `.env`, or in committed config **must** move
   to `credentials/manager.py` (keyring + env var fallback) — flag this
   explicitly to the user, it's a real security fix, not just style.
5. Verify the same way as Scaffold mode (`uv sync && pytest && doctor`), plus
   confirm any behavior that existed before the refactor still produces the
   same result.

## Non-negotiables (apply in both modes)

These are the parts of `reference/architecture.md` most likely to get
skipped under time pressure — check them explicitly:

- Every command has a human mode and a `--json` mode; agents must never be
  forced to parse decorated human output.
- Errors are raised as `CliError` subclasses with a stable `code`, and follow
  the exit-code table in `reference/conventions.md` — never a bare
  `sys.exit(1)` or an unstructured stack trace as the user-facing failure.
- No secret ever gets written to project-local config (`.{{package}}/config.toml`
  is safe to commit). Secrets only live in the OS keychain or env vars.
- `doctor` and the bundled `skills/<package_name>/SKILL.md` are not optional
  extras — every generated/refactored CLI ships both.
- Run `scripts/install_hooks.sh` once per checkout (`.git/hooks/` isn't
  versioned). It installs a non-blocking pre-commit warning
  (`scripts/check_command_docstrings.py`) for command docstrings drifting
  from the code they document — those docstrings are the `--help` text
  agents read.
- Prefer `pathlib`/`shutil`/`platformdirs` over shelling out or hardcoded
  POSIX paths — the whole point is that it runs unmodified on macOS, Linux
  and Windows.
