---
id: IDEA-311
title: 'Standard: the full gate runs in Gitea CI after the push, not as Antagor''s
  gate_command'
created: '2026-10-21T04:37:47+00:00'
source_project: antagor
source_path: /Users/bolandau/Work/antagor
status: taken
for_path: /Users/bolandau/Work/tools/cli-generator
task: CG-054
taken_project: cli-generator
linked: true
---

The Human 21.10: for now the standard for every package is the semkit/dataio way. [publish] has no gate_command: publish runs no full gate on the Mac (no machine queue); deploy_command pushes main with tags; Gitea CI on homeserver runs the full gate after the push. Known cost: a red CI comes after the tag. Change the template (template/.agents/antagor/antagor.toml.jinja, AGENTS.md.jinja, README.md.jinja, CODING_STANDARDS.md.jinja, .gitea/workflows/ci.yml.jinja), the standard and the skill's Update mode (a migration step: drop gate_command), and cli-generator's own antagor.toml. A gate before the tag (Antagor waits for the CI status of a pushed candidate) is in Antagor's backlog, taken only if a red tag after release happens.
