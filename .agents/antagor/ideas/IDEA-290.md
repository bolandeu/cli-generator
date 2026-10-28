---
id: IDEA-290
title: 'Optional extra bundled skills: data/skills/<name>/SKILL.md served by skill
  install'
created: '2026-10-20T10:25:52+00:00'
source_project: ''
source_path: /Users/bolandau/Work/products/mediagen
status: dropped
for_path: /Users/bolandau/Work/tools/cli-generator
triage:
  serves: []
  risks: []
  why: 'Real need (mediagen): process skills per media kind cannot ship today, so
    the package would patch a template file and conflict on every copier update; optional,
    nothing changes for packages without extra skills'
  score: 5.0
  route: task
  at: '2026-10-20T10:26:03+00:00'
reason: taken as CG-041
---

MediaGen (rb-mediagen, cli mediagen) needs process skills per media kind (og-image, video, logo) besides the conventions SKILL.md; they call the CLI and hold no logic. Today they cannot ship: skill install and --ai serve only data/SKILL.md, and skills in the repo's .agents/skills/ are not in the wheel. Proposal, optional (most packages have none; nothing changes for them): extra skills in src/<pkg>/data/skills/<name>/SKILL.md (Agent Skills format, name <cli>-<name>); skill install installs the main skill plus every extra one (--skill <name> for one), skill list shows them; describe --json lists them; the test checks frontmatter and that no skill lists commands. Without it MediaGen patches commands/skill.py, a template file, and resolves conflicts on every copier update.
