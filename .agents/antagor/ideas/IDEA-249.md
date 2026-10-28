---
id: IDEA-249
title: Remove tools-watch from the standard
created: '2026-10-19T05:54:10+00:00'
source_project: cli-generator
source_path: /Users/bolandau/Work/tools/cli-generator
status: epic
for_path: /Users/bolandau/Work/tools/cli-generator
triage:
  serves: []
  risks: []
  why: Contract with sysadmin accepted by the Human 2026-10-19; package agents apply
    it through cli-builder Update mode.
  score: 2.0
  route: clarify
  at: '2026-10-19T05:59:56+00:00'
clarify_project: /Users/bolandau/Work/tools/cli-generator
clarify_since: '2026-10-19T05:59:56+00:00'
epic: E-003
before_epic: clarifying
---

architecture.md mentions tools-watch (release.py exit 3, auth status reader); no such tool exists (sysadmin, 2026-10-19). Remove or reword. Contract docs/contracts/sysadmin.md, accepted by the Human 2026-10-19.
