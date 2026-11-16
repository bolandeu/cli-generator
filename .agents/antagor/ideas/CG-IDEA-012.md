---
id: CG-IDEA-012
title: 'Standard, Database: a package''s own db module next to the db part'
created: '2026-11-08T10:09:38+00:00'
source_project: cli-generator
source_path: /Users/bolandau/Work/tools/cli-generator
status: dropped
triage:
  serves: []
  risks: []
  why: 'The plan extraction found this still true today; the idea names one concrete
    fix, small enough for one task: Standard, Database: a package''s own db module
    next to the db part'
  score: 2.0
  route: task
  at: '2026-11-08T14:15:35+00:00'
reason: 'These add rules or gate strictness without removing work from the package
  author: the goal is a package that makes writing a CLI as simple as possible.'
confirmed: мне не нужны лишние бесполезные идеи важно - наш пакет должен максимально
  просто давать писать cli а не усложнять
---

From the CG-082 extraction of docs/plans/freeze-list.md (F5.1 a package's own `core/db.py` or `commands/db.py` collides with the `db` part).

Still open: Standard, Database, "Turn on" names no case of an existing module of the package

Suggested: Standard, Database: a package's own db module next to the db part
