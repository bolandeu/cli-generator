---
id: IDEA-247
title: 'Template CI runs in Gitea Actions: .gitea/workflows/ci.yml'
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

Gitea Actions runs only .gitea/workflows/; the template ships .github/workflows/ci.yml, so no CLI except semkit has CI. Move the workflow to .gitea/workflows/ (runner label docker, cache ci-cache; sample: semkit, bolandeu/repo-sync-smoke uv-probe.yml). Contract docs/contracts/sysadmin.md, accepted by the Human 2026-10-19.
