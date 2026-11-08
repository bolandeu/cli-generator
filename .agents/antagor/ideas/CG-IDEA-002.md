---
id: CG-IDEA-002
title: 'x-rb-skills[]: add the skill path, drop the extra call'
created: '2026-11-08T09:02:34+00:00'
source_project: mcp
source_path: /Users/bolandau/Work/tools/mcp
status: epic
benefit: 'rb-mcp serves each CLI''s skill text as an MCP resource without a second
  process: resource://<cli>/skill/<name> reads the path straight from the describe
  document it already has. Every MCP client gets the guidance the CLI wrote.'
triage:
  serves: []
  risks: []
  why: rb-mcp serves a CLI's skill text as an MCP resource without a second process
    once the describe document carries the installed path.
  score: 2.0
  route: task
  at: '2026-11-08T09:24:54+00:00'
epic: E-009
before_epic: new
---

In x-rb-skills[] each entry carries name and description today. Add path: the absolute path of the installed skill directory (or the SKILL.md file), resolved the same way 'skill install' resolves it. The consumer then needs no '<cli> skill path' call and no second process.

Shape: {"name": "serp", "description": "...", "path": "/Users/.../.pi/agent/skills/serp"}

Empty or absent when the skill part is off (include_skill = false): the consumer treats it as 'no skill resource'. Chosen over a 'skill path' command by the Architect of cli-generator (option b).
