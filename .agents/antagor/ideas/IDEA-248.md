---
id: IDEA-248
title: Our packages depend on each other through the Gitea registry, not git tags
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
  score: 3.0
  route: clarify
  at: '2026-10-19T05:59:56+00:00'
clarify_project: /Users/bolandau/Work/tools/cli-generator
clarify_since: '2026-10-19T05:59:56+00:00'
epic: E-003
before_epic: clarifying
---

architecture.md §8 pins our packages by git tag in [tool.uv.sources]. Renovate and tool-updater's reinstall of dependents work with the Gitea PyPI index (explicit = true, rb-x>=...). Rewrite §8 and the template for the registry. Contract docs/contracts/sysadmin.md, accepted by the Human 2026-10-19.
