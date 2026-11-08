---
id: IDEA-255
title: 'CG-026 dropped the osv-scanner install from template CI: in Gitea CI the gate''s '
created: '2026-10-19T06:16:45+00:00'
source_project: cli-generator
source_path: /Users/bolandau/Work/tools/cli-generator
status: dropped
for_path: /Users/bolandau/Work/tools/cli-generator
found_in_epic: E-003
triage:
  serves: []
  risks: []
  why: In remote CI the gate's vulnerability audit is skipped; if CG-IDEA-001 removes
    the remote CI the idea is moot, otherwise the workflow must install osv-scanner
    (it is on this machine, so the local gate audits).
  score: 1.0
  route: task
  at: '2026-11-08T09:25:46+00:00'
reason: Циай должен быть либо удаленный, либо локальный
confirmed: Циай должен быть либо удаленный, либо локальный
---

CG-026 dropped the osv-scanner install from template CI: in Gitea CI the gate's vulnerability audit is now always skipped with a notice. Install osv-scanner in the workflow (cached in /cache/bin, like uv) so CI audits uv.lock again.
