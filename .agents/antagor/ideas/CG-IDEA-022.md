---
id: CG-IDEA-022
title: 'Standard, Technology: parallel code takes its worker count from the machine'
created: '2026-11-08T10:09:49+00:00'
source_project: cli-generator
source_path: /Users/bolandau/Work/tools/cli-generator
status: new
---

From the CG-082 extraction of docs/plans/freeze-list.md (F14.1 parallel code and the machine's size: a candidate Recommended rule).

Still open: Standard, Technology has no rule on a worker count; the template CI sets no `PYTEST_XDIST_AUTO_NUM_WORKERS`

Suggested: Standard, Technology: parallel code takes its worker count from the machine
