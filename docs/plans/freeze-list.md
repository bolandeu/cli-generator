# Freeze list

The template, the gate and the Standard are frozen from v1.26.0, released 2026-10-21 (the Human, 2026-10-21). Only a defect that
makes a package fail the gate or CI, or work wrongly, is fixed (a v1.26.x patch). Everything else waits here
until the Human lifts the freeze.

- Standard, Release: the line "`antagor publish` runs no full gate before the tag" is out of date — the
  remote gate (CI on the candidate branch, before the tag) exists now.
- The gate tag is written in 6 places of a package (Antagor `checks`, CI workflow, README, AGENTS.md, two
  tests), so every gate bump is a task. One source (the CI gate line), the others compared with it.
- The package CI workflow runs on `main` and tags only; the remote gate needs it on `antagor/publish-*` too.
- `check_template.sh` checks the gate on Python 3.11 by rewriting a rendered package with `sed`; a small
  3.11 fixture package would be simpler.
- `rb-release check --keep-going`: list every red step in one run (a package probe took 7 runs).
- Template modules without a module docstring (27); Antagor now names them in the worker's brief.
