---
id: CG-IDEA-004
title: 'describe: x-rb-type/default/multiple and hidden in the Standard'
created: '2026-11-08T09:21:24+00:00'
source_project: llmkit
source_path: /Users/bolandau/Work/tools/llmkit
status: new
benefit: the template and the Standard agree, consumers stop guessing
---

From the llmkit architect, after comparing live describe --json across llm, hostme, serp, context and reading the template at v1.27.3.

1. x-rb-type: Mandatory on every option and argument; vocabulary is Typer type names (boolean, str, int, float, choice, path, file, datetime, int range, float range); a new name is additive.
2. x-rb-default: Mandatory and always present — the value, or null when there is no default or it is computed at run time. The current template omits the key when the default is None, a callable or () (lldmkit sees this as a gap, the Architect of cli-generator confirmed it as a template bug).
3. x-rb-multiple: present iff repeatable or variadic; absent means single.
4. Gate step: read the package own describe --json, fail on a param entry without x-rb-type, with an unknown type name, or without an x-rb-default key.
5. Standard text: a hidden command, option or argument serializes hidden: true; absent means visible (template has it since v1.5.0 with a schema test; the Standard does not name it).

On the llmkit side: LLMKIT-027 re-syncs its hand-copied opencli.py from v1.5.6 to v1.27.3; when the template ships points 1-4 llmkit bumps to that tag in a follow-up task.
