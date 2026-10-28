---
id: IDEA-266
title: 'cli-builder Update mode: a worker cannot commit before copier update'
created: '2026-10-19T14:05:32+00:00'
source_project: semkit
source_path: /Users/bolandau/Work/tools/semkit
status: taken
for_path: /Users/bolandau/Work/tools/cli-generator
triage:
  serves: []
  risks: []
  why: Update mode tells a worker to commit before copier update; the worker hook
    forbids commit, so every package worker improvises around copier's dirty-tree
    guard
  score: 6.0
  route: task
  at: '2026-10-19T14:06:14+00:00'
task: CG-036
taken_project: cli-generator
---

From semkit SEMKIT-065: Update mode steps 13.1 and 14.1 say to commit before copier update, but an Antagor worker may not run git commit (hook). The worker staged the tree (git add -A) and ran copier.run_update from Python with only the dirty-tree guard off; copier reads the index, so nothing was lost. Name this way in the skill (or a ready command), so workers do not improvise.
