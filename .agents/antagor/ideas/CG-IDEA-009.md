---
id: CG-IDEA-009
title: the db part ships no example table inside the package's own `core/tables.py`
created: '2026-11-08T10:09:34+00:00'
source_project: cli-generator
source_path: /Users/bolandau/Work/tools/cli-generator
status: new
triage:
  serves: []
  risks: []
  why: 'The plan extraction found this still true today; the idea names one concrete
    fix, small enough for one task: the db part ships no example table inside the
    package''s own `core/tables.py`'
  score: 2.0
  route: task
  at: '2026-11-08T14:15:32+00:00'
---

From the CG-082 extraction of docs/plans/freeze-list.md (F4.4 template example tables merge into `tables.py` as duplicates).

Still open: `template/src/*/core/tables.py` still ships `items`, `responses` and the views as examples

Suggested: the db part ships no example table inside the package's own `core/tables.py`
