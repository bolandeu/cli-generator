---
id: CG-IDEA-007
title: 'check_template.sh: a 3.11 fixture package instead of sed rewriting a rendered
  one'
created: '2026-11-08T10:09:32+00:00'
source_project: cli-generator
source_path: /Users/bolandau/Work/tools/cli-generator
status: new
triage:
  serves: []
  risks: []
  why: 'The plan extraction found this still true today; the idea names one concrete
    fix, small enough for one task: check_template.sh: a 3.11 fixture package instead
    of sed rewriting a rendered one'
  score: 2.0
  route: task
  at: '2026-11-08T14:15:30+00:00'
---

From the CG-082 extraction of docs/plans/freeze-list.md (F1.1 `check_template.sh` rewrites a rendered package with `sed` for its 3.11 round).

Still open: the `sed` rewrite is still there (`scripts/check_template.sh`, `run_gate_on_python_311`); the gate still declares `requires-python = ">=3.11"`

Suggested: check_template.sh: a 3.11 fixture package instead of sed rewriting a rendered one
