# cli-generator

Claude Code plugin: a `cli-builder` skill that scaffolds new CLI tools or
refactors existing ones onto one shared architecture (Python + uv + Typer,
project-aware config, OS-keychain credentials, dual human/JSON output,
AI-readable errors, an `HttpProvider` base for external APIs, enforced
`min_version`, versions from git tags + towncrier changelog fragments per
the shared release standard, one local gate — `scripts/release.py --check` —
that also proves the built wheel installs and reports the right version,
`auth status --check --json` in a cross-tool shape, and an enforced
`--help` contract).

## Layout

```
.claude-plugin/plugin.json    # plugin manifest
skills/cli-builder/           # the skill: SKILL.md + reference docs
copier.yml                    # copier config; _subdirectory points at template/
template/                     # the actual copier template
```

## Using the skill

From the target package's directory, load this plugin for the session:

```bash
claude --plugin-dir /path/to/cli-generator
```

(or symlink it into `~/.claude/skills/cli-generator` to auto-load every
session without the flag), then ask for either:

- "create a CLI for X" → scaffold mode
- "refactor this script/package into our CLI architecture" → refactor mode
  (works on a feature branch, never directly on main — see SKILL.md step 0)

Both modes end by offering to publish: the skill prepares the local repo
and hands it to the root tools agent, which creates a **private** GitHub
repo and pushes after your yes; the skill then verifies that
`uv tool install "git+https://github.com/<owner>/<repo>.git"` works from
there — the one-command install every generated README/SKILL.md points
other machines (and agents) at. Nothing reaches GitHub without your go-ahead.

If it doesn't trigger automatically, invoke it explicitly:
`/cli-generator:cli-builder`.

See `skills/cli-builder/SKILL.md` for the exact workflow, and
`skills/cli-builder/reference/architecture.md` /
`skills/cli-builder/reference/conventions.md` for the contract every
generated package must satisfy.

## Using the template directly

```bash
# `gh:bolandeu/cli-generator` in place of `.` works from anywhere (add
# `--vcs-ref v1.0.0` to pin a template release)
uvx copier copy . <dest-dir> \
  --data package_name=mycli \
  --data project_name="My CLI" \
  --data description="Project-aware automation CLI" \
  --data author_name="Your Name"
cd <dest-dir>
uv sync
uv run mycli --help
uv run pytest
```

Once a project has been generated this way, pulling in later architecture
changes is `cd <dest-dir> && copier update` (requires the destination to be
a git repo — copier uses git to diff and merge template changes without
clobbering your business logic). Template releases are git tags on this
repo (`v1.0.0`, ...): `copier update` moves a project from the tag it was
generated with to the newest one, and re-runs the same verify loop
afterwards is how you know the merge was clean.
