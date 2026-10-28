---
id: IDEA-362
title: 'skill install: copy whole skill folders; let a CLI choose the default scope'
created: '2026-10-27T16:02:27+00:00'
source_project: mediagen
source_path: /Users/bolandau/Work/products/mediagen
status: dropped
for_path: /Users/bolandau/Work/tools/cli-generator
triage:
  serves: []
  risks: []
  why: 'Freeze: no package breaks today (only mediagen ships skill extras and departs);
    waits in docs/plans/freeze-list.md'
  score: null
  route: clarify
  at: '2026-10-27T16:03:28+00:00'
clarify_project: /Users/bolandau/Work/tools/cli-generator
clarify_since: '2026-10-27T16:03:28+00:00'
reason: 'Deferred, not rejected: template freeze; kept in cli-generator docs/plans/freeze-list.md
  and taken up when the freeze lifts'
---

From mediagen (ADR 0019). The template's `skill install` writes only the SKILL.md text, so a skill with references/, scripts/, assets/, LICENSE or NOTICE loses them; it should copy each bundled skill folder whole. Also let a CLI choose its default scope (mediagen installs into the project by default, into .agents/skills and .claude/skills at once, user level only with --user), instead of user level and one tool per call. mediagen departs from the template on this until the template takes the change.
