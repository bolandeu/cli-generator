---
id: IDEA-240
title: 'Browser help for every CLI: describe that InSpectra renders, a shared clidocs
  wrapper'
created: '2026-10-18T12:23:11+00:00'
source_project: semkit
source_path: /Users/bolandau/Work/tools/semkit
status: epic
for_path: /Users/bolandau/Work/tools/cli-generator
triage:
  serves: []
  risks: []
  why: 'Human decision 2026-10-18: HTML help for every CLI; template describe gives
    an empty InSpectra page; several design choices (docs vs describe, clidocs home,
    examples test) need an epic'
  score: 6.0
  route: clarify
  at: '2026-10-18T12:40:26+00:00'
clarify_project: /Users/bolandau/Work/tools/cli-generator
clarify_since: '2026-10-18T12:40:26+00:00'
epic: E-001
before_epic: clarifying
---

Decision of the Human (2026-10-18): human help of every CLI is an HTML page with search built by InSpectra (NuGet InSpectra.Gen, .NET; inspectra render file html FILE --out-dir DIR) from the CLI's OpenCLI document, by one shared wrapper clidocs TOOL -> ~/Work/tools/docs/TOOL/index.html (no env var, no per-project config). To standardize in cli-generator. Gaps of the template describe (core/opencli.py; seen in semkit, wordstat, serp): 1) commands nested under a root key command, InSpectra expects them at the root (empty page without a jq rewrite); 2) Example lines stay in description, OpenCLI has an examples field; 3) option explanations repeated in the description; 4) defaults/allowed values only in x-rb-* metadata, no arity maximum, so every option shows as repeatable; 5) subcommands of a pipeline command (semkit read steps) do not carry the parent's input arguments, so the composer builds commands with no input. describe is a cross-tool contract: choose a versioned fix of describe or a separate human docs output (semkit SEMKIT-054 adds semkit docs for semkit only; align with it). CLIs without describe: bukvarix, antagor, hostme, sitelayout. Current wrapper: TOOL describe | jq 'if .command then {opencli, info} + (.command|del(.name)) else . end' > f.json; DOTNET_ROOT=/opt/homebrew/opt/dotnet/libexec ~/.dotnet/tools/inspectra render file html f.json --out-dir ~/Work/tools/docs/TOOL. sysadmin offers dotnet/InSpectra on homeserver and a tools.toml entry if clidocs becomes a tool.
