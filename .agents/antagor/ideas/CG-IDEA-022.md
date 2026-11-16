---
id: CG-IDEA-022
title: 'Standard, Technology: parallel code takes its worker count from the machine'
created: '2026-11-08T10:09:49+00:00'
source_project: cli-generator
source_path: /Users/bolandau/Work/tools/cli-generator
status: dropped
triage:
  serves: []
  risks: []
  why: 'The plan extraction found this still true today; the idea names one concrete
    fix, small enough for one task: Standard, Technology: parallel code takes its
    worker count from the machine'
  score: 2.0
  route: task
  at: '2026-11-08T14:15:45+00:00'
reason: 'These add rules or gate strictness without removing work from the package
  author: the goal is a package that makes writing a CLI as simple as possible.'
confirmed: мне не нужны лишние бесполезные идеи важно - наш пакет должен максимально
  просто давать писать cli а не усложнять
---

From the CG-082 extraction of docs/plans/freeze-list.md (F14.1 parallel code and the machine's size: a candidate Recommended rule).

Still open: Standard, Technology has no rule on a worker count; the template CI sets no `PYTEST_XDIST_AUTO_NUM_WORKERS`

Suggested: Standard, Technology: parallel code takes its worker count from the machine
