---
id: IDEA-250
title: 'Gate finds secrets: gitleaks in release.py --check, .env* in .gitignore'
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
  score: 4.0
  route: clarify
  at: '2026-10-19T05:59:56+00:00'
clarify_project: /Users/bolandau/Work/tools/cli-generator
clarify_since: '2026-10-19T05:59:56+00:00'
epic: E-003
before_epic: clarifying
---

No secret scan before push; Gitea repos are readable by everyone in the tailnet. Add gitleaks to release.py --check (skip with a notice when not installed, like osv-scanner) and .env* to template/.gitignore. Contract docs/contracts/sysadmin.md, accepted by the Human 2026-10-19.
