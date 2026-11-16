---
id: CG-IDEA-018
title: 'Standard, Release: `deploy.sh` and `deploy_command` for a package not from
  the template'
created: '2026-11-08T10:09:44+00:00'
source_project: cli-generator
source_path: /Users/bolandau/Work/tools/cli-generator
status: dropped
triage:
  serves: []
  risks: []
  why: 'The plan extraction found this still true today; the idea names one concrete
    fix, small enough for one task: Standard, Release: `deploy.sh` and `deploy_command`
    for a package not from the template'
  score: 2.0
  route: task
  at: '2026-11-08T14:15:41+00:00'
reason: 'These add rules or gate strictness without removing work from the package
  author: the goal is a package that makes writing a CLI as simple as possible.'
confirmed: мне не нужны лишние бесполезные идеи важно - наш пакет должен максимально
  просто давать писать cli а не усложнять
---

From the CG-082 extraction of docs/plans/freeze-list.md (F9.1 a package not from the template has no `scripts/deploy.sh`, and a hand commit cannot add it).

Still open: merged with F9.2: Standard, Release says what a version does, not what a hand-made package puts in `[publish]`

Suggested: Standard, Release: `deploy.sh` and `deploy_command` for a package not from the template
