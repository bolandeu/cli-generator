---
id: CG-IDEA-015
title: '`gate_status_url` names the package''s Gitea repo, not its GitHub mirror'
created: '2026-11-08T10:09:41+00:00'
source_project: cli-generator
source_path: /Users/bolandau/Work/tools/cli-generator
status: new
---

From the CG-082 extraction of docs/plans/freeze-list.md (F6.1 `gate_status_url` takes the repository name from `repository_url` (the GitHub mirror)).

Still open: `template/.agents/antagor/antagor.toml.jinja` still renders the last path segment of `repository_url`

Suggested: `gate_status_url` names the package's Gitea repo, not its GitHub mirror
