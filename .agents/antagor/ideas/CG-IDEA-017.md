---
id: CG-IDEA-017
title: 'existing package: a help test pins `COLUMNS`, `NO_COLOR` and `TERM`'
created: '2026-11-08T10:09:43+00:00'
source_project: cli-generator
source_path: /Users/bolandau/Work/tools/cli-generator
status: new
triage:
  serves: []
  risks: []
  why: 'The plan extraction found this still true today; the idea names one concrete
    fix, small enough for one task: existing package: a help test pins `COLUMNS`,
    `NO_COLOR` and `TERM`'
  score: 2.0
  route: task
  at: '2026-11-08T14:15:40+00:00'
---

From the CG-082 extraction of docs/plans/freeze-list.md (F8.2 help snapshots need the render env pinned in conftest).

Still open: the template pins it inside `tests/test_help.py`; `existing-package.md` does not name it for a package's own test

Suggested: existing package: a help test pins `COLUMNS`, `NO_COLOR` and `TERM`
