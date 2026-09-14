# cli-generator

Claude Code plugin: a `cli-builder` skill that scaffolds new CLI tools or
refactors existing ones onto one shared architecture (Python + uv + Typer,
project-aware config, OS-keychain credentials, dual human/JSON output,
AI-readable errors).

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

If it doesn't trigger automatically, invoke it explicitly:
`/cli-generator:cli-builder`.

See `skills/cli-builder/SKILL.md` for the exact workflow, and
`skills/cli-builder/reference/architecture.md` /
`skills/cli-builder/reference/conventions.md` for the contract every
generated package must satisfy.

## Using the template directly

```bash
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
clobbering your business logic).
