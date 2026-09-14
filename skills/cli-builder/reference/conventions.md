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

## Exit codes (fixed across all generated CLIs)

```
0  Success
1  General error
2  Invalid arguments
3  Authentication error
4  Project not initialized
```

Implemented as `CliError` subclasses in `core/errors.py`:
`ProjectNotInitialized` → 4, `AuthRequired` → 3, `InvalidArguments` → 2,
anything else unexpected → let it be a plain `CliError("...", exit_code=1)`
or, for truly unexpected exceptions, let them surface as tracebacks (exit
1) rather than swallowing them silently — only expected, named failure
modes get a `CliError`.

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

## Command surface every generated CLI starts with

```
<cli> init [--name] [--force] [--non-interactive]
<cli> status [--json]
<cli> doctor [--json]
<cli> config get|set|list
<cli> auth login|logout|status
<cli> skill install [--tool claude-code|agents] [--project]
<cli> run
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
