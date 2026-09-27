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
cd /tmp/cli-gen-test && uv sync -q && uv run ruff check . && uv run ruff format --check . \
  && uv run ty check && uv run pytest -q
```

Also regenerate once with `--data include_auth=false` and run the same
loop — this branch drops `commands/auth.py`, `credentials/` and
`tests/test_auth.py` via `copier.yml`'s templated `_exclude`, and it's easy
to change `cli.py.jinja`/`commands/`/tests in a way that only the
`include_auth=true` branch was ever exercised with.

`ruff format --check` runs on generated projects with the template's
`line-length = 120`. To format template sources in place, run it with that
config explicitly — `template/pyproject.toml.jinja` isn't a real
`pyproject.toml`, so a bare `ruff format template/` silently uses the
88-column default and rewraps every file:

```bash
uvx ruff format --line-length 120 template/src template/scripts
```

For the distribution + release path (`scripts/release.py`, tag pinning),
verify against a local bare remote rather than assuming: `git init --bare
/tmp/remote.git`, add it as `origin` in the generated project, commit,
`git tag -a v0.1.0 -m v0.1.0` (`uv run <cli> --version` must now print
`0.1.0`, not `0.0.0…`), push `main` with `-u`, add a fragment
(`uv run towncrier create +x.fixed.md -c x`), commit, run
`uv run scripts/release.py patch`, `git push --follow-tags`, then
`uv tool install "git+file:///tmp/remote.git@v0.1.1"` and `<cli> --version`.
The release process itself is specified in
`~/Projects/tools/docs/standard-release.md` (owned by the tools/ root
agent) — change it there first, then here.

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
  `commands/auth.py`/`credentials/`/`tests/test_auth.py`, `cli.py.jinja`
  conditionally skips importing/registering `auth`, and `doctor.py`
  detects the module at runtime (`importlib.util.find_spec`) instead of
  being templated. If you touch any of these, regenerate with
  `include_auth=false` and run the full verify loop — this combination
  previously went untested and silently shipped a `ModuleNotFoundError` on
  `keyring` for anyone who picked "no auth".
- `_exclude` patterns in `copier.yml` match the **rendered** path
  (`tests/test_auth.py`), not the template file name
  (`tests/test_auth.py.jinja`) — a pattern with `.jinja` matches nothing
  and the file is silently generated anyway.
- Typer ≥ 0.27 no longer depends on `click` (it ships its own parser and
  `typer.Exit`/`typer.Abort` in `typer.exceptions`). Don't `import click`
  in template code — it isn't installed in generated projects. Related:
  `no_args_is_help=True` exits 2, which is why `cli.py.jinja` and
  `output.group()` implement help-on-no-args by hand.
- `output.guard` must re-raise `typer.Exit`/`typer.Abort` before its
  catch-all `except Exception` — both subclass `RuntimeError`, so a plain
  catch-all would turn every controlled exit into an `UNEXPECTED` error.
- Template release tags must be valid PEP 440 versions (`v1.1.0`,
  `v1.2.0rc1`). copier silently ignores anything else (`v1.1.0-test`) when
  picking the latest version, so `copier update` reports nothing to do.
- `copier update` refuses to run on a dirty tree, so every artifact a tool
  in the generated project writes must be in `template/.gitignore`
  (`.coverage` from pytest-cov was missed once and blocked updates).
  When adding a dev tool, run it once and check `git status` is clean.
