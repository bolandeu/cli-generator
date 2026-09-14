# AGENTS.md

Guidance for agents working on **this repo** — the `cli-generator` Claude
Code plugin itself (not a package it generated; that has its own
`AGENTS.md` from `template/AGENTS.md.jinja`).

## What this is

A plugin bundling one skill, `cli-builder`, that scaffolds new CLI tools or
refactors existing ones onto a shared Python/Typer/uv architecture. See
`README.md` for layout, `skills/cli-builder/SKILL.md` for the skill's
workflow, and `skills/cli-builder/reference/architecture.md` for the
contract every generated package must satisfy.

## Where the spec lives (don't duplicate it)

- `skills/cli-builder/reference/architecture.md` — the shape contract
  (layers, storage locations, credential model, safety/dry-run rules,
  distribution).
- `skills/cli-builder/reference/conventions.md` — exact JSON envelope,
  error codes, exit codes, global options. Verbatim, not per-project.
- `skills/cli-builder/reference/refactor-checklist.md` — migration order
  for Refactor mode.
- The short coding-quality rules (think first, simplicity, surgical
  changes, goal-driven execution) live inline in `SKILL.md` itself, not in
  a separate file — don't re-split them out.

If you're changing what generated CLIs look like, change `architecture.md`
and `template/` together, in the same commit — a template change that
contradicts the documented contract is a bug.

## Testing a change to `template/`

Never trust a template edit without regenerating and running it — a
Jinja/copier mistake fails silently as literal `{{ package_name }}` text
in generated files, not as an error.

```bash
rm -rf /tmp/cli-gen-test
uvx copier copy . /tmp/cli-gen-test \
  --data package_name=demotool --data project_name="Demo" \
  --data description="d" --data author_name="A" --data include_auth=true \
  --defaults --trust -q
cd /tmp/cli-gen-test && uv sync -q && uv run ruff check . && uv run pytest -q
```

Also regenerate once with `--data include_auth=false` and run the same
`uv sync -q && uv run ruff check . && uv run pytest -q` — this branch drops
`commands/auth.py` and `credentials/` via `copier.yml`'s templated
`_exclude`, and it's easy to change `cli.py.jinja`/`commands/`/tests in a way
that only the `include_auth=true` branch was ever exercised with.

For a change touching `.claude-plugin/plugin.json`, also run:

```bash
claude plugin validate . --strict
```

For a change to the `copier update` story (versioning), verify with a
real git-based round trip (tag v1, generate, edit a template file, tag v2,
`copier update` in the generated project) rather than assuming it works —
see this repo's history for the exact sequence; it has broken silently
before (missing answers file, wrong `copier.yml` location).

## Known sharp edges (don't reintroduce these)

- `copier.yml` must live at the **repo root**, not inside `template/`, with
  `_subdirectory: template`. Copier 9.x has no `--subdirectory` CLI flag —
  this is the only way to keep `template/` separate from the plugin's own
  `skills/`/`.claude-plugin/` at generation time.
- `template/{{ _copier_conf.answers_file }}.jinja` must exist, or copier
  never writes `.copier-answers.yml` and `copier update` silently can't
  work on generated projects.
- Only files with a `.jinja` suffix get Jinja-rendered by copier (and only
  path names always get rendered). A plain `.py` file that needs
  `package_name` should derive it dynamically —
  `__name__.split(".")[0]` — instead of becoming a `.jinja` file; keep
  `.jinja` files to the minimum that genuinely need answer substitution
  (`pyproject.toml`, `README.md`, `AGENTS.md`, `data/SKILL.md`, the answers
  file).
- Keep `output.guard`'s local-flag merge dict and `output.JsonOption` /
  `output.DryRunOption` etc. in sync if you add a new global option that
  commands should also accept locally (`<cli> <command> --flag`, not just
  `<cli> --flag <command>`).
- `include_auth=false` must actually remove the auth surface, not just the
  `keyring` dependency: `copier.yml`'s `_exclude` drops
  `commands/auth.py`/`credentials/`, and `cli.py.jinja` conditionally skips
  importing/registering `auth`. If you touch either, regenerate with
  `include_auth=false` and run the full verify loop — this combination
  previously went untested and silently shipped a `ModuleNotFoundError` on
  `keyring` for anyone who picked "no auth".
