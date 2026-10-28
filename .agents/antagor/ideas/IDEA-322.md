---
id: IDEA-322
title: Gate on Python >=3.11 with the CI color fix (semkit waits for the tag)
created: '2026-10-21T06:34:13+00:00'
source_project: semkit
source_path: /Users/bolandau/Work/tools/semkit
status: taken
for_path: /Users/bolandau/Work/tools/cli-generator
task: CG-060
taken_project: cli-generator
linked: true
---

semkit's remote gate is red on Gitea CI: 'standard: commands' does not see the Commands heading through Rich's ANSI color under GITHUB_ACTIONS (run 320, job 508). Fixed in v1.25.7, which needs Python >=3.14; CG-060 brings the gate back to >=3.11. semkit SEMKIT-071 waits for that release. Please link this idea to CG-060 (antagor idea link).
