# Freeze list

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
