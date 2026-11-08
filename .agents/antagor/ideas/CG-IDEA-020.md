---
id: CG-IDEA-020
title: the gate refuses a `[tool.uv.sources]` git URL for one of our packages
created: '2026-11-08T10:09:47+00:00'
source_project: cli-generator
source_path: /Users/bolandau/Work/tools/cli-generator
status: new
triage:
  serves: []
  risks: []
  why: 'The plan extraction found this still true today; the idea names one concrete
    fix, small enough for one task: the gate refuses a `[tool.uv.sources]` git URL
    for one of our packages'
  score: 2.0
  route: task
  at: '2026-11-08T14:15:43+00:00'
---

From the CG-082 extraction of docs/plans/freeze-list.md (F10.1 a dependency by a GitHub git URL passes the local gate and fails CI at `uv sync`; no gate step catches it).

Still open: Standard, Install recommends the Gitea registry; `gate/rb_release/gate.py` checks only explicit-index sources. Related to IDEA-248

Suggested: the gate refuses a `[tool.uv.sources]` git URL for one of our packages
