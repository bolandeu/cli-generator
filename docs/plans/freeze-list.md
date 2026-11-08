# Freeze list

> Extracted 2026-11-08 by task CG-082: every item below has a verdict and a
> candidate idea title in that task's report. This file is a source record, not
> a plan; it stays until the Human confirms the extraction.

The template, the gate and the Standard are frozen from v1.26.0, released 2026-10-21 (the Human, 2026-10-21). Only a defect that
makes a package fail the gate or CI, or work wrongly, is fixed (a v1.26.x patch). Everything else waits here
until the Human lifts the freeze.

- `check_template.sh` checks the gate on Python 3.11 by rewriting a rendered package with `sed`; a small
  3.11 fixture package would be simpler.
- The remote gate exits 124 when the runner is busy longer than `gate_timeout_minutes` (15); a queue of ~10 min
  already happened. A repeat `publish` works; a larger timeout would avoid the repeat.
- A package with a browser (Playwright, spider) needs in its CI: `uvx playwright@<locked> install --with-deps chromium`,
  container `--shm-size=1g`, `CRAWLEE_DISABLE_BROWSER_SANDBOX=1` (the job runs as root). Each such package wrote it
  by hand; a note in the Standard, CI, would save the next one five red runs.
- Update flow (`existing-package.md`), gaps found by batches 2–3 (2026-10-23): `copier update` needs `git stash -u`
  first and `--trust` always; changing an option (`include_project=false`) deleted an edited package file
  (`core/services.py`): check `git status | grep '^ D'`; a conflict next to a reworded comment drops a package block;
  template example tables merge into `tables.py` as duplicates; template tests assume the default project folder; the
  gate's pytest step runs with CI colour variables and help/describe snapshots may hold a Mac data-dir path; a
  leaked key in history: a fingerprint-only `.gitleaksignore` line (accepted, not yet in the Standard); old
  `.git/hooks/pre-commit` with only the docstring check can be deleted; the docstring checker flags a ctx-only
  signature change; `skills.frontmatter()` keeps YAML quotes; doctor checks with `status` ok/warn/fail.
- Update flow, batch 4 (2026-10-23): a package's own `core/db.py` or `commands/db.py` collides with the `db` part;
  `errors.py` keeps the Database* errors without `include_db`; files a package deleted (`core/deps.py`) stay deleted
  though new template code imports them; `AGENTS.md` is not written when `CLAUDE.md` exists; the 3.11 → 3.14 jump
  needs ruff fixes (UP047, `except (A, B)`); rich elides long option names under the CI env; `uv.lock` changes are
  not in the conflict list; README install lines are the package's to fix (`_skip_if_exists`).
- `gate_status_url` in the Antagor config takes the repository name from `repository_url` (the GitHub mirror, e.g.
  dataio's `rb-dataio`), not from the folder; a new package whose mirror name differs gets a wrong gate URL and
  fixes it by hand. Rendering `{{ antagor_name }}` there is not a fix: on update it would rewrite existing
  packages' correct URLs to the command (gsc). Needs an update-safe default like `antagor_name` (2026-10-23).
- Gate, contracts step: under pytest-xdist (`-n auto` in addopts) `-vv` prints `[gw0] [ 50%] PASSED
  tests/test_contracts.py::test_contract[x]`, which `_CONTRACT_RESULT` doesn't match: the summary says '0 cases'.
  Pass/fail is still the return code, so only the text is wrong. Fix: run the step with `-p no:xdist`, or accept
  both line forms (semkit, 2026-10-24; semkit works around it in its conftest).
- Gate loop for a package not from the template (`existing-package.md`), batch 5 (2026-10-24): the CI workflow's gate
  line has the tag pasted by hand (no `_commit`); help snapshots need the render env pinned in conftest (the template's
  test_help does it itself); a stale `.git/hooks/pre-commit` from an old `install_hooks.sh` stops `antagor new` and
  agents' classifiers block removing it (the Human does); the Antagor config of such a package has no `[publish]`
  block (`gate = "remote"`, `gate_status_url`, `deploy_command`; semver is written by `antagor new` since a082910) — copied by hand;
  a library's install step is not spelled out.
- Batch 5, more: a package not from the template has no `scripts/deploy.sh`, and a hand commit can't add it (hook:
  a hand fix only changes existing files); without `deploy_command` `antagor publish` tags locally and pushes nothing
  (google-oauth uses `deploy_command = "git push origin main --follow-tags"`); the template ci.yml comment names
  `.copier-answers.yml`; no library variant of AGENTS.md/CI in the docs; `task-create` needs `--no-epic --confirmed`
  without an epic, and the Antagor config is edited by the Architect on main, not by a worker through owns.
- Batch 5, more: a dependency on our package by a git URL on GitHub passes the local gate but fails CI at `uv sync`
  (no GitHub credentials on the runner); no gate step catches it, so "Dependencies on our packages" is tied to no
  red step (wordpress-bulk-editor, yandex-webmaster moved to the Gitea index by hand). Fixing a package before
  `antagor new` leaves those commits out of the first changelog.
- Update under Antagor (mediagen, 2026-10-24): the Architect's files that conflict
  (Antagor config, AGENTS.md, CODING_STANDARDS.md) get the template side on main by the Architect, then the task
  merges main; the template side of the Antagor config drops a project's own `worker` and extra `checks` — keep them.
- Batch 5, llmkit: the CI runner's lowest Python is 3.11.2, where an `except*` re-raise is wrapped in an
  ExceptionGroup (local 3.11.14 passes); the gate's missing-`doctor` step was not in my brief's red list (the brief
  listed steps, not causes); `antagor publish --main` does not merge a task in `publish` (`antagor publish <id>`).
- Update under Antagor (semkit, 2026-10-26): an update replaces the project's own copies of template tests
  (test_ci, test_scripts) — the gate lists them as removed/changed existing tests, say so; `task-create` needs each
  `[check: …]` to equal a `--check` string and counts `--read-first` with the body's "Read first" (max 5); a Renovate
  PR left open by a hand update closes itself on Renovate's next run.
- Parallel work vs machine size (antagor, incident 2026-10-26: semkit `-n auto` × 3 workers = 30 processes with word
  vectors, the Mac hung): candidate Recommended rule — code that runs work in parallel takes its worker count from
  free memory and cores, an env var lowers it, a process that loads a large model states its memory per worker; the
  template CI could set PYTEST_XDIST_AUTO_NUM_WORKERS. Not now: only semkit uses xdist (SEMKIT-088 caps it in a
  `pytest_xdist_auto_num_workers` hook); Antagor caps its workers' env.
- CI load per release (sysadmin, 2026-10-27): the template workflow runs on push to `main`, `antagor/publish-*` and
  tags `v*`, and `antagor publish` pushes one commit to all three — three identical 15–20 min gates per release on a
  2-slot runner; a queued publish-branch run outlasts Antagor's 15 min remote-gate wait (bukvarix v0.6.2 failed that
  way). Dropping the `tags` trigger is safe (the tag's commit is already gated); `main` stays for hand pushes.
- Gate step times (antagor, 2026-10-27): Antagor reads CI job steps and logs, but the whole gate is one workflow
  step. Not split in the workflow (it would copy the gate's step list into every package). Antagor now times each
  step from Gitea's per-line log stamps, with no gate change — keep the `<tool>: <check> ... <result>` line format,
  Antagor parses it. semkit's 525 s: pytest 191 s, `standard: errors` 159 s, `standard: commands` 130 s (164
  commands, each run with --help and with a bad option), wheel 31 s. Candidate: run the per-command Standard
  checks in one process or in parallel.
