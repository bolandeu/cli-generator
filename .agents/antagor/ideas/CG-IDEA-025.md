---
id: CG-IDEA-025
title: Take the shape of semkit docs (OpenCLI, commands at the root) as the reference
  of the template docs command
created: '2026-11-13T18:26:29+00:00'
source_project: semkit
source_path: /Users/bolandau/Work/tools/semkit
status: new
benefit: 'the template gets a measured shape of a docs command instead of inventing
  one: one document from the step docstrings, OpenCLI with the commands at the root,
  already built and shipped in semkit'
triage:
  serves: []
  risks: []
  why: The template's docs command has no measured reference shape; semkit already
    ships one (OpenCLI, commands at the root), so copying it avoids inventing a second
    shape and lets semkit drop its own copy after a copier update. Waits until semkit's
    own docs command is accepted there.
  score: 2.0
  route: task
  at: '2026-11-14T18:30:54+00:00'
---

From docs/plans/html-and-brief.md (now docs/research/2026-10-28-html-and-brief.md §Browser help, SEMKIT-091), the note kept as IDEA-240 there: cli-generator takes the shape of SEMKIT-054 `semkit docs` as the reference. After SEMKIT-054 is accepted, send it a sample of `semkit docs` output; when the template ships its own docs output, semkit moves to it by copier update and drops its own code.
