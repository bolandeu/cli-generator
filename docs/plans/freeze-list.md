# Freeze list

The template, the gate and the Standard are frozen from v1.26.0, released 2026-10-21 (the Human, 2026-10-21). Only a defect that
makes a package fail the gate or CI, or work wrongly, is fixed (a v1.26.x patch). Everything else waits here
until the Human lifts the freeze.

- `check_template.sh` checks the gate on Python 3.11 by rewriting a rendered package with `sed`; a small
  3.11 fixture package would be simpler.
- The remote gate exits 124 when the runner is busy longer than `gate_timeout_minutes` (15); a queue of ~10 min
  already happened. A repeat `publish` works; a larger timeout would avoid the repeat.
