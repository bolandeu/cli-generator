# Freeze list

The template, the gate and the Standard are frozen from v1.26.0, released 2026-10-21 (the Human, 2026-10-21). Only a defect that
makes a package fail the gate or CI, or work wrongly, is fixed (a v1.26.x patch). Everything else waits here
until the Human lifts the freeze.

- Standard, Release: the line "`antagor publish` runs no full gate before the tag" is out of date — the
  remote gate (CI on the candidate branch, before the tag) exists now.
- The gate tag is written in 6 places of a package (Antagor `checks`, CI workflow, README, AGENTS.md, two
  tests), so every gate bump is a task. One source (the CI gate line), the others compared with it.
- `check_template.sh` checks the gate on Python 3.11 by rewriting a rendered package with `sed`; a small
  3.11 fixture package would be simpler.
- `rb-release check --keep-going`: list every red step in one run (a package probe took 7 runs).
- Template modules without a module docstring (27); Antagor now names them in the worker's brief.
- The remote gate exits 124 when the runner is busy longer than `gate_timeout_minutes` (15); a queue of ~10 min
  already happened. A repeat `publish` works; a larger timeout would avoid the repeat.
- Generated tests pin Antagor's own settings (`checks`, the ignore file's lines, the prefix rule); each Antagor
  change broke packages (v1.26.4–v1.26.6). Test only the package's facts (gate, docstring check), not Antagor's.
- `init --help` says it creates `.{cli}/config.toml`, but the folder is named by the package (`.rb_mediagen/`,
  not `.mediagen/`): wrong only when the command name differs from the package name.
