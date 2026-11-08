---
id: CG-IDEA-003
title: Discovery by distribution name, not by binary name — the describe inventory
  was short by three packages
created: '2026-11-08T09:08:20+00:00'
source_project: mcp
source_path: /Users/bolandau/Work/tools/mcp
status: new
benefit: 'The inventory of describable CLIs in your answers (14 CLI, 650 commands)
  is short: llmkit, wordpress-bulk-editor and mediagen answer describe --json too.
  A correct number keeps the ''every installed package appears'' check honest and
  stops a standard-wide rule being written from a wrong sample.'
triage:
  serves: []
  risks: []
  why: Consumers filter family membership by binary prefix and lose rb-llmkit, rb-wordpress-bulk-editor
    and rb-mediagen; the Standard never says membership is the distribution name.
  score: 2.0
  route: task
  at: '2026-11-08T09:24:56+00:00'
---

Measured on this machine (macOS, 2026-11-08), by distribution name from 'uv tool list':

  rb-llmkit v0.14.11                binary llm        -> describe ok, 34 leaf commands, template v1.5.6
  rb-wordpress-bulk-editor v5.1.2   binary wp-bulk    -> describe ok, 20 leaf commands
  rb-mediagen v0.9.0                binary mediagen   -> describe ok, 26 leaf commands
  rb-repo-sync-smoke v0.1.1         binary rb-smoke   -> no describe (exit 2), correctly skipped

Your message listed llm, wp-bulk, mediagen and rb-smoke as 'non-rb binaries in the same bin dir', so they were counted neither as family members nor as describable. The cause is matching on the entrypoint name: the distribution is rb-*, the binary is not. A consumer that filters by binary prefix loses three packages; one that filters by distribution name (uv tool list) gets all four.

Suggestion for the standard (docs or the describe contract): state that family membership is the DISTRIBUTION name rb-*, and that a tool's own name is x-rb-tool.tool — the two differ (llmkit: dist rb-llmkit, tool llm, binary llm; wordpress-bulk-editor: dist rb-wordpress-bulk-editor, tool wp-bulk). Also worth a line in the gate: a package whose entrypoint name does not match its distribution is legal and common, so nothing may derive the one from the other.

Totals on this machine: 17 packages answer describe --json, ~730 leaf commands; skipped with a reason: ym, ywm, sitemap-xml (No such command describe, exit 2), rb-repo-sync-smoke; sitelayout not installed.
