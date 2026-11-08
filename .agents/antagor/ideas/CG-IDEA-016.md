---
id: CG-IDEA-016
title: 'gate, consumer contracts: the summary survives pytest-xdist'
created: '2026-11-08T10:09:42+00:00'
source_project: cli-generator
source_path: /Users/bolandau/Work/tools/cli-generator
status: new
---

From the CG-082 extraction of docs/plans/freeze-list.md (F7.1 the contracts step misses `[gw0]` lines under pytest-xdist).

Still open: `gate/rb_release/gate.py`, `_CONTRACT_RESULT`, and its `-vv` run has no `-p no:xdist`

Suggested: gate, consumer contracts: the summary survives pytest-xdist
