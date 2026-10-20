# Conventions: exact envelope, codes, exit statuses

Reuse these verbatim in every generated/refactored CLI. Do not invent a
different shape per project — the whole point is that an agent that has
seen one of these CLIs already knows how every other one behaves.

## JSON success envelope

```json
{
  "ok": true,
  "...command-specific fields": "..."
}
```

## JSON error envelope

```json
{
  "ok": false,
  "error": {
    "code": "AUTH_REQUIRED",
    "message": "Authentication is required for provider 'openai'.",
    "action": "Run 'mycli auth login'."
  }
}
```

`action` is optional but should be present whenever there's a concrete next
command the caller (human or agent) can run to unblock itself.

## JSON report envelope (data that can also be a problem)

A command whose output is a report — `auth status` (`architecture.md` §4), a health or audit command — emits the data **whether or not** it
found a problem, via `output.emit_report(ctx, payload, render_human, problem)`:

```json
{"ok": true,  "tool": "mycli", "credentials": [...]}
{"ok": false, "error": {"code": "CREDENTIALS_UNHEALTHY", "message": "...", "action": "..."},
 "tool": "mycli", "credentials": [...]}
```

`problem=None` → exactly the success envelope. A `CliError` → `ok: false`,
the standard `error` object **next to** the full payload, and the process
exits with that error's exit code. Don't hand-roll this per command: a
consumer relies on `ok` meaning "exit code 0" and on the
report fields being there in both cases.

## `describe --json`: the tool's contract as an OpenCLI document

`<cli> describe --json` prints an [OpenCLI](https://opencli.org) document
(spec 0.1) — the one command whose `--json` is **not** in the `{"ok": ...}`
envelope: the bare document, on one line, so it validates against the
OpenCLI schema as it is. The tools catalog and the platform read it from
every installed tool.

- `command` tree, `options`, `arguments`, `required`, `aliases`, `hidden`,
  `acceptedValues` — introspected from Typer/Click (`core/opencli.py`),
  never written by hand.
- `arity` of each option and argument: `minimum` and `maximum` (`maximum`
  is absent for a repeatable one).
- `exitCodes` on the root — from `core/errors.py` `EXIT_CODES` (the table
  below).
- What OpenCLI has no field for goes into `metadata` as `x-rb-*`:
  per option/argument `x-rb-type`, `x-rb-default`, `x-rb-multiple`; on the
  root command `x-rb-tool` (`tool`, `dist`, `package`),
  `x-rb-template-version`, `x-rb-env` (credential env vars from the
  providers, the database's from `core/db.py` `ENV_VARS`), `x-rb-data`
  (`tables` with `schema` and `kind`, `<tool>_v1_*` `views`, files in `user_data_dir`),
  `x-rb-external` (`[[tool.rb.external]]`).

`tests/test_describe.py` validates it against the vendored schema
(`tests/data/opencli.schema.json`), checks it against the registered
commands and their `--help`, and snapshots it
(`tests/snapshots/describe.json`). It is public API like everything here.

## Exit codes (fixed across all generated CLIs)

`core/errors.py` `EXIT_CODES` is this table in code (`describe`'s
`exitCodes`); a `CliError` with a code not in it fails the tests.

```
0  Success
1  General error (incl. UNEXPECTED and ABORTED)
2  Invalid arguments
3  Authentication error
4  Project not initialized
5  Provider error (external service: network, timeout, 5xx, 429, bad body)
6  CLI too old for this project or database (cli.min_version, a newer schema)
```

## Error codes

All `CliError` subclasses live in `core/errors.py`; don't invent a code
per project when one of these fits:

| `error.code`                   | exit | raised by |
|--------------------------------|------|-----------|
| `INVALID_ARGUMENTS`            | 2    | any command; also `--non-interactive` without `--confirm` |
| `AUTH_REQUIRED`                | 3    | a provider getting 401/403, or a service with no credential |
| `PROJECT_NOT_INITIALIZED`      | 4    | `services.require_project_root` |
| `PROVIDER_ERROR`               | 5    | `providers.HttpProvider` after retries; carries `provider` and `status` |
| `CLI_TOO_OLD`                  | 6    | `services.load_config` when installed < `cli.min_version`; `core.db` when the shared database is at a revision this release doesn't know |
| `DATABASE_UNAVAILABLE`         | 5    | `core.db` when `<TOOL>_DATABASE_URL` is set but unreachable, rejected or not PostgreSQL (never a fallback to SQLite) |
| `DATABASE_NOT_MIGRATED`        | 1    | `core.db` when the shared database is behind this release's migrations (`<cli> db upgrade`) |
| `DEPENDENCY_TOO_OLD`           | 1    | `core.deps.require_cli` when another CLI this one calls is missing or older than needed |
| `CREDENTIALS_UNHEALTHY`        | 3    | `auth status` when a required credential isn't ok, or any is invalid/expired (envelope also carries the full report) |
| `CREDENTIAL_STORE_UNAVAILABLE` | 1    | `credentials.manager` on write/delete when the keychain is unusable |
| `ABORTED`                      | 1    | the user answered "no" to `require_confirmation` |
| `EXAMPLE_OUTSIDE_PATH`         | 1    | `core.docs` (`<cli> docs`) when a docstring example does not start with its command path |
| `UNEXPECTED`                   | 1    | `output.guard` — any exception nobody mapped |

`UNEXPECTED` is the safety net, not a design: every command goes through
`output.guard`, which turns an escaped exception into this envelope so a
`--json` caller still gets JSON (with `action: "Re-run with --verbose..."`
— the traceback goes to stderr only under `--verbose`). When one shows up
repeatedly for the same cause, that cause deserves its own `CliError`.

## stdout / stderr

- **stdout is data only**: the JSON envelope (success *or* error) under
  `--json`; the human rendering of a *successful* result otherwise.
- **stderr is everything else**: human-mode `Error:` lines, `--verbose`
  progress (`output.vecho`), `logging` output (WARNING and above always,
  DEBUG under `--verbose`), tracebacks.

So `<cli> status > out.json` never captures an error as data, and an agent
under `--json` parses stdout and reads stderr only to debug. Under
`--json`, the error envelope stays on stdout on purpose — one stream to
parse, and `ok: false` + exit code say it's an error.

A usage error — an unknown option or command, a missing argument, a bad
value — is Click's, raised before any command runs. Under `--json`
(anywhere before `--`) it is the same envelope: `INVALID_ARGUMENTS`, exit
2 (the root group `output.RootGroup`); without `--json` it stays Click's
usage message on stderr. The gate's `standard: errors` step probes every
command with an unknown option for exactly this.

## No-args = help, not a usage error

`<cli>` alone and `<cli> <group>` alone (`<cli> config`, `<cli> auth`)
print their help and exit **0**. Click/Typer's default is a "Missing
command" usage error with exit 2 — wrong for a CLI agents explore by
poking at it. The template's root callback and `output.group()` implement
this; every new group must be created with `output.group(...)`, not
`typer.Typer(...)`.

## Global options every command inherits

```
--project PATH        explicit project root (skips cwd-walk discovery)
--json                 machine-readable output
--quiet                suppress non-essential human output
--verbose              extra diagnostic output
--non-interactive       never prompt; fail with a CliError instead
--dry-run               preview a state-changing command without acting
--confirm               skip the confirmation prompt for a destructive command
--version
--ai                    print the bundled agent skill doc and exit
--help
```

`--dry-run` and `--confirm` are relevant only to commands that change
external state — see `architecture.md` §10. Any such command must accept
both; `output.is_dry_run`/`output.require_confirmation` implement the
check, don't hand-roll it per command.

## What counts as a breaking change

Everything in this file is public API: the envelope shape, error codes,
exit codes, global options, command names and flags. Versions follow
SemVer against that surface (`architecture.md` §8):

Everything above also includes the `auth status` report (`architecture.md`
§4) and the `describe --json` document. From `1.0.0` on:

| Change | Bump |
|---|---|
| bug fix, no surface change | patch `1.2.1` |
| new command/flag/field, old behaviour intact | minor `1.3.0` |
| anything removed, renamed or changed: command, flag, `--json` shape, exit code, error code | major `2.0.0` |

While at `0.x` (Cargo/uv convention — matches the `>=0.2,<0.3` pins other
tools use for us):

| Change | Bump |
|---|---|
| bug fix **or** new command/flag/field, old behaviour intact | patch `0.2.1 → 0.2.2` |
| anything removed, renamed or changed (breaking) | minor `0.2 → 0.3` |

Deprecate before removing: keep the old form working with a warning on
stderr, name the deprecation in the ticket title, remove it in the next
breaking release.

## Command surface every generated CLI starts with

```
<cli> init [--name] [--force] [--non-interactive]
<cli> status [--json]
<cli> doctor [--json]
<cli> config get|set|list
<cli> auth login|logout
<cli> auth status [--check] [--provider NAME] [--json]   # fixed shape: architecture.md §4
<cli> skill install [--tool claude-code|agents] [--project]
<cli> run
<cli> describe [--json]                                   # OpenCLI document, no envelope
<cli> docs [--out FILE]                                   # OpenCLI document for people (help-standard.md)
<cli> --ai
```

Extra commands for a specific project's task are added alongside these, not
instead of them — `status`/`doctor`/`auth` are the load-bearing diagnostic
surface an agent reaches for first.

Both `--json`/`--quiet` are wired as *both* a global option (before the
subcommand: `<cli> --json status`) and a local option on every leaf command
(after it: `<cli> status --json`) — an agent shouldn't have to know which
form a given CLI accepts. See the template's `output.guard`/`output.JsonOption`
for how this is kept from being copy-pasted per command.

## Language of help and output

Command help (docstrings, `help=`), human-mode messages and `error.message` /
`action` are written in **English** in the template. A project may translate
its own commands' help and human output (e.g. Russian for Russian-speaking
users) — consistently across the whole CLI, not command by command. Never
translate anything machine-read: JSON keys, enum values (`status: "ok"`,
`source: "env"`), `error.code`, exit codes, command and flag names. The
template's `auth status` text stays English unless the project translates it
like any other command (its snapshot will show the change).

## Discovery: a bare `<cli>` is the command reference

`<cli>` with no arguments prints `<name> <version> — <description>`,
then every command with the first line of its docstring; `<cli> <command>
--help` prints the full docstring and options. That is the command
documentation — it can't drift from the code because it's rendered from
it. Nothing else (SKILL.md, README) lists commands.

Shape every command's help the same way:

```python
@output.guard
def status(ctx: typer.Context, json_output: bool = output.JsonOption) -> None:
    """Show the current project's status.        <- one-line summary (the bare-<cli> listing)

    Optional paragraph: what it does, what it changes, when to use it.

    Example: {cli} status --json                 <- required; `{cli}` becomes the CLI name
    """
```

- Every parameter is a `typer.Option(...)`/`typer.Argument(...)` with a
  non-empty `help=` (the shared `output.*Option` ones already have it).
- Prefer a literal docstring. A computed help text is allowed only as a
  module-level `command.__doc__ = f"..."` right after the function (the
  docstring check reads that expression; `{cli}` isn't substituted there —
  use `cli_name()` in the f-string). Setting `__doc__` anywhere else
  (inside a function, via a decorator, in another module) is not allowed:
  the hooks can't see it.
- Commands live in `src/<package>/commands/*.py`; a different layout sets
  `[tool.cli-generator] commands = ["<glob>", ...]` in `pyproject.toml`.
- Every group is created with `output.group("<description>")`.
- Changing a command's behaviour means updating its docstring in the same
  commit and refreshing `tests/snapshots/help/` with
  `uv run pytest --snapshot-update`. Hooks and tests enforce all of this —
  `architecture.md` §5.

## Two ways an agent gets usage docs without prior context

1. `skills/<package_name>/data/SKILL.md` bundled into the installed package
   (not just the source repo) — installed into an AI tool's own skill
   directory via `<cli> skill install --tool claude-code|agents [--project]`.
2. `<cli> --ai` — prints that same bundled doc to stdout, for an agent that
   can execute the CLI but can't read files from disk (sandboxed shell,
   remote exec with no filesystem access to the installed skill).

Keep these in sync: there is one canonical copy
(`src/<package_name>/data/SKILL.md`), both paths read from it — never
duplicate the content.
