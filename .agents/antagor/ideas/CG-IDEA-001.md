---
id: CG-IDEA-001
title: 'No Gitea CI in the standard: Gitea only stores releases that passed the local
  gate'
created: '2026-10-29T04:32:58+00:00'
source_project: antagor
source_path: /Users/bolandau/Work/antagor
status: new
benefit: No remote test runs on the server (the Human 29.10); one gate, the local
  one; new tools stop getting a CI that duplicates it
---

The Human, 29.10: «Удалённого CI быть не должно», «на удалённом Gitea только хранились выпуски, не включались тесты и полные прогоны», «нагрузка там только прод-версии, прошедшие гейт». Today the template gives every tool .gitea/workflows/ci.yml that repeats rb-release check on the Gitea runner on each push and tag (21 tools and mediagen have it); cli-generator's own release gate was remote (template-gate.yml, gate_status_url) — Antagor's Architect switched its antagor.toml to gate = local with gate_command = sh scripts/check_template.sh (commit 187cea7, not pushed: a push runs the CI). Wanted: (1) the template no longer generates .gitea/workflows/ci.yml and the standard and ADR 0005 say the local gate is the only one; (2) remove cli-generator's template-gate.yml and the tests of its CI (tests/test_repo_ci.py); (3) roll the removal of ci.yml out to the existing tools through the template update; (4) then sysadmin turns the runners off. Releases stay: deploy.sh pushes main with tags.
