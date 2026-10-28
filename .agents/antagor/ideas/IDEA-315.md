---
id: IDEA-315
title: 'Package rules: the Architect''s hand fix for the smallest changes'
created: '2026-10-21T05:09:06+00:00'
source_project: antagor
source_path: /Users/bolandau/Work/antagor
status: taken
for_path: /Users/bolandau/Work/tools/cli-generator
task: CG-058
taken_project: cli-generator
linked: true
---

The Human 21.10: the hand fix must be written in the rules for new packages. Antagor now lets the Architect commit a hand fix with no task: no new behaviour and no test change, at most 2 existing text or config files (*.md, *.toml, *.yaml, *.yml, .gitea/, .github/) and 10 changed lines, no path an active task owns; the pre-commit hook checks it and journals architect.hand_fix; it goes out with the next antagor publish --main. Bounds: [architect.hand_fix] in antagor.toml (guarded by the Human's antagor architect floor-accept). Put it in the template's AGENTS.md.jinja and CODING_STANDARDS.md.jinja (when a change is a hand fix, when it is a task: code under src/template/gate or a test or a rule's meaning is always a task), and in the Standard; the skill's Update mode needs no step (it is Antagor's default).
