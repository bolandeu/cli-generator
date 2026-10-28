---
id: IDEA-372
title: 'skill install: whole skill folders into the project, both harness dirs at
  once'
created: '2026-10-28T08:33:54+00:00'
source_project: mediagen
source_path: /Users/bolandau/Work/products/mediagen
status: dropped
for_path: /Users/bolandau/Work/tools/cli-generator
reason: 'Duplicate of IDEA-362, deferred: template freeze; details added to cli-generator
  docs/plans/freeze-list.md, taken up when the freeze lifts'
---

mediagen (ADR 0019) departs from the template skill part: `skill install` copies each bundled skill folder whole (SKILL.md, references/, scripts/, assets/, LICENSE, NOTICE), into the project by default, into .agents/skills/ and .claude/skills/ at once; --user for the user level; --tool and --project go. A reinstall replaces each <cli>* skill folder whole (stale files removed) and never touches other skills. Reason: skills of several files break when only SKILL.md text is copied; a project keeps the skills its outputs were made with. If the template takes this, mediagen drops its own copy of commands/skill.py on the next template update.
