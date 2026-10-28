---
id: IDEA-255
title: 'CG-026 dropped the osv-scanner install from template CI: in Gitea CI the gate''s '
created: '2026-10-19T06:16:45+00:00'
source_project: cli-generator
source_path: /Users/bolandau/Work/tools/cli-generator
status: new
for_path: /Users/bolandau/Work/tools/cli-generator
found_in_epic: E-003
---

CG-026 dropped the osv-scanner install from template CI: in Gitea CI the gate's vulnerability audit is now always skipped with a notice. Install osv-scanner in the workflow (cached in /cache/bin, like uv) so CI audits uv.lock again.
