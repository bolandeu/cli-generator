---
id: CG-IDEA-016
title: 'gate, consumer contracts: the summary survives pytest-xdist'
created: '2026-11-08T10:09:42+00:00'
source_project: cli-generator
source_path: /Users/bolandau/Work/tools/cli-generator
status: new
triage:
  serves: []
  risks: []
  why: 'The plan extraction found this still true today; the idea names one concrete
    fix, small enough for one task: gate, consumer contracts: the summary survives
    pytest-xdist'
  score: 2.0
  route: task
  at: '2026-11-08T14:15:39+00:00'
---

From the CG-082 extraction of docs/plans/freeze-list.md (F7.1 the contracts step misses `[gw0]` lines under pytest-xdist).

Still open: `gate/rb_release/gate.py`, `_CONTRACT_RESULT`, and its `-vv` run has no `-p no:xdist`

Suggested: gate, consumer contracts: the summary survives pytest-xdist
