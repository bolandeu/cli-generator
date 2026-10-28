---
id: IDEA-254
title: Shared code of packages in one library (rb-cli-core) so a standard update is
  a dependency bump
created: '2026-10-19T05:55:55+00:00'
source_project: cli-generator
source_path: /Users/bolandau/Work/tools/cli-generator
status: epic
for_path: /Users/bolandau/Work/tools/cli-generator
triage:
  serves: []
  risks: []
  why: 'Standard updates without merge conflicts. Human 2026-10-19: improve, never
    break; the move to the library and every later contract update must be steps in
    the cli-builder skill (Refactor/Update modes) that package agents follow.'
  score: 3.0
  route: clarify
  at: '2026-10-19T05:56:37+00:00'
clarify_project: /Users/bolandau/Work/tools/cli-generator
clarify_since: '2026-10-19T05:56:37+00:00'
epic: E-004
before_epic: clarifying
---

Today the template copies shared code (output, credentials, gate) into every package; copier update conflicts where a package edited it. Move shared code into a library pinned via the Gitea registry; Renovate bumps it, no merge conflicts; template stays thin. Human, 2026-10-19: it must improve, not break - no package behaviour change, migration package by package, old packages keep working until migrated. First: search for ready solutions.
