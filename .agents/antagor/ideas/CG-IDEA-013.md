---
id: CG-IDEA-013
title: the Database* errors ship only with the db part
created: '2026-11-08T10:09:39+00:00'
source_project: cli-generator
source_path: /Users/bolandau/Work/tools/cli-generator
status: epic
triage:
  serves: []
  risks: []
  why: 'The plan extraction found this still true today; the idea names one concrete
    fix, small enough for one task: the Database* errors ship only with the db part'
  score: 2.0
  route: task
  at: '2026-11-08T14:15:36+00:00'
epic: E-014
before_epic: new
---

From the CG-082 extraction of docs/plans/freeze-list.md (F5.2 `errors.py` keeps the Database* errors without `include_db`).

Still open: `template/src/*/core/errors.py` ships `DatabaseUnavailable`, `DatabaseNotMigrated`, `DatabaseTooNew` in every package

Suggested: the Database* errors ship only with the db part
