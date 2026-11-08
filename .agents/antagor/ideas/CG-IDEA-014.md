---
id: CG-IDEA-014
title: 'update flow: a template module the package deleted comes back when new code
  imports it'
created: '2026-11-08T10:09:40+00:00'
source_project: cli-generator
source_path: /Users/bolandau/Work/tools/cli-generator
status: new
---

From the CG-082 extraction of docs/plans/freeze-list.md (F5.3 files a package deleted (`core/deps.py`) stay deleted though new template code imports them).

Still open: `core/deps.py` is imported by `commands/doctor.py` and `core/opencli.py`; `existing-package.md` names no such case

Suggested: update flow: a template module the package deleted comes back when new code imports it
