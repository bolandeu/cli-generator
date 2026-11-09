---
id: CG-IDEA-011
title: '`core/skills.frontmatter()` strips a matching pair of YAML quotes'
created: '2026-11-08T10:09:36+00:00'
source_project: cli-generator
source_path: /Users/bolandau/Work/tools/cli-generator
status: new
triage:
  serves: []
  risks: []
  why: 'The plan extraction found this still true today; the idea names one concrete
    fix, small enough for one task: `core/skills.frontmatter()` strips a matching
    pair of YAML quotes'
  score: 2.0
  route: task
  at: '2026-11-08T14:15:34+00:00'
---

From the CG-082 extraction of docs/plans/freeze-list.md (F4.10 `skills.frontmatter()` keeps YAML quotes).

Still open: `core/skills.py::frontmatter` returns `value.strip()`, quotes included

Suggested: `core/skills.frontmatter()` strips a matching pair of YAML quotes
