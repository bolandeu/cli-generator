---
id: CG-IDEA-010
title: 'check_command_docstrings: a `ctx`-only signature change is not a logic change'
created: '2026-11-08T10:09:35+00:00'
source_project: cli-generator
source_path: /Users/bolandau/Work/tools/cli-generator
status: new
triage:
  serves: []
  risks: []
  why: 'The plan extraction found this still true today; the idea names one concrete
    fix, small enough for one task: check_command_docstrings: a `ctx`-only signature
    change is not a logic change'
  score: 2.0
  route: task
  at: '2026-11-08T14:15:33+00:00'
---

From the CG-082 extraction of docs/plans/freeze-list.md (F4.9 the docstring checker flags a `ctx`-only signature change).

Still open: `template/scripts/check_command_docstrings.py` dumps `node.args` whole

Suggested: check_command_docstrings: a `ctx`-only signature change is not a logic change
