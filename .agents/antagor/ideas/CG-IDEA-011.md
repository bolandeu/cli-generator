---
id: CG-IDEA-011
title: '`core/skills.frontmatter()` strips a matching pair of YAML quotes'
created: '2026-11-08T10:09:36+00:00'
source_project: cli-generator
source_path: /Users/bolandau/Work/tools/cli-generator
status: new
---

From the CG-082 extraction of docs/plans/freeze-list.md (F4.10 `skills.frontmatter()` keeps YAML quotes).

Still open: `core/skills.py::frontmatter` returns `value.strip()`, quotes included

Suggested: `core/skills.frontmatter()` strips a matching pair of YAML quotes
