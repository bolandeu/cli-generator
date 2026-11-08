---
id: CG-IDEA-024
title: 'ci.yml: pin actions/checkout to a SHA, not a mutable tag'
created: '2026-11-08T10:39:10+00:00'
source_project: mcp
source_path: /Users/bolandau/Work/tools/mcp
status: new
benefit: Every generated package inherits the same CI step; a mutable tag means a
  compromised or moved upstream tag runs in all of them. A SHA pin closes it once,
  in the template.
---

Advisory from rb-mcp's first publish (v0.1.0, 2026-11-08):

  .gitea/workflows/ci.yml:26:      - uses: actions/checkout@v4

v4 is a mutable tag. The rest of the file is already strict (pinned osv-scanner 2.7.0 and gitleaks 8.30.1, a pinned gate command derived from .copier-answers.yml).

Ask: pin the SHA (with the version in a comment, e.g. actions/checkout@<sha> # v4.2.2) so a moved tag cannot change what runs in every package's gate. A package cannot fix this itself: the workflow is template-owned and copier overwrites it.
