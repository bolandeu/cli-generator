---
id: CG-IDEA-026
title: 'typer 0.29 dropped click: the template''s opencli.py breaks on a fresh install'
created: '2026-11-16T06:40:37+00:00'
source_project: llmkit
source_path: /Users/bolandau/Work/tools/llmkit
status: new
benefit: 'A package generated from the template and installed fresh (uv tool install
  from a tag) gets typer 0.29.1 from PyPI, where click is gone: opencli._param_meta
  reads param.type, so describe --json answers UNEXPECTED AttributeError TyperOption
  has no attribute type. mcp already caps typer>=0.27,<0.29; the template''s pyproject.toml.jinja
  says only typer>=0.12, so every generated package has the same trap under an unbounded
  dependency.'
triage:
  serves: []
  risks: []
  why: The cap typer>=0.27,<0.29 in v1.27.9 already keeps this door shut, but opencli.py
    reads click attributes (param.type, secondary_opts) that typer 0.29 no longer
    has, so this is exactly what blocks supporting 0.29 later; running describe --json
    in the fresh-install step is what would catch it.
  score: 3.0
  route: task
  at: '2026-11-16T06:41:23+00:00'
---

A package generated from the template and installed fresh (uv tool install from a git tag) resolves typer 0.29.1 from PyPI. Typer 0.29 no longer ships click (import click fails), and core/opencli.py reads click's attributes — param.type in _param_meta, param.secondary_opts, param.nargs, param.metavar. So llm describe --json answers ok:false, UNEXPECTED, AttributeError: 'TyperOption' object has no attribute 'type'. The repo itself does not see it: uv.lock holds typer 0.27.2, and the gate's build+install step only runs llm --version and llm --help.

Evidence: llmkit v0.14.12 and v0.14.13 both fail this way when installed from a tag with typer 0.29.1; mcp/pyproject.toml already pins typer>=0.27,<0.29, semkit pins <0.28.

Ask: decide in the template — an upper bound on typer in pyproject.toml.jinja (as mcp does), or support 0.29 in opencli.py by not touching click attributes; and a gate step that runs describe --json on the freshly installed wheel, not only --version and --help.
