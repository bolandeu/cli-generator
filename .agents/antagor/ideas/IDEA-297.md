---
id: IDEA-297
title: 'Gate: --json from the root''s help counts; errors probe <cli> --json <path>
  --unknown'
created: '2026-10-20T14:31:51+00:00'
source_project: semkit
source_path: /Users/bolandau/Work/tools/semkit
status: taken
for_path: /Users/bolandau/Work/tools/cli-generator
task: CG-045
taken_project: cli-generator
linked: true
---

Agreed with cli-generator on 2026-10-20 (SEMKIT-068): in 'standard: json' a command takes --json when its own help or the root's help lists it; 'standard: errors' probes '<cli> --json <command path> --unknown'. semkit's 145 chained pipeline steps under 'semkit read' fail both rules today and pass with this change (checked by hand: 'semkit --json read ad-groups --bogus-x' -> INVALID_ARGUMENTS, exit 2). Release a template tag; semkit SEMKIT-068 waits for it.
