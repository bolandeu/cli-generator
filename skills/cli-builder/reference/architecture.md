# Architecture contract

Every CLI produced by this skill follows the same shape. This is what makes
packages generated months apart, by different sessions, still consistent.

## 1. CLI ≠ project

The CLI is a stable interface; a project using it only holds config/data.
The CLI package lives in its own repo, is installed once
(`uv tool install <pkg>`), and is used by any number of unrelated project
directories:

```
mycli v0.8
  ↓ installed once
project-a/.mycli/config.toml
project-b/.mycli/config.toml
project-c/.mycli/config.toml
```

Never vendor the CLI's own `.venv`/source into a consuming project unless
that project *is* the CLI's own dev checkout.

### Distribution: develop locally, install from GitHub — no PyPI required

The intended lifecycle is: develop on one machine, push to a GitHub repo,
then install that exact package on any other machine (any OS) straight
from the repo:

```bash
uv tool install "git+https://github.com/<owner>/<repo>.git"
```

No PyPI publish step is needed for this to work — `uv tool install`
resolves and builds directly from the git URL. Pin a version by appending
`@<tag-or-branch>`. This is wired into every generated package
automatically: the `repository_url` copier question fills in this exact
command in both `README.md` (for the human) and
`src/{{ package_name }}/data/SKILL.md` (for an agent that finds the skill
installed on a machine before the CLI binary itself is — e.g. a synced
`~/.claude/skills/` directory reaching a fresh machine ahead of the tool).
If `repository_url` was left blank at generation time, both files carry a
`<owner>/<repo>` placeholder to fill in once the repo exists.

## 2. Four layers

```
CLI (commands/)      — argument parsing, --json/--help, nothing else
  ↓
Core (core/)         — services, models, errors: the real business logic
  ↓
Providers / Filesystem / Credentials
  — providers/    external APIs, LLMs, etc. (Provider protocol)
  — core/services  project filesystem state (.{{package}}/config.toml)
  — credentials/   OS keychain + env vars, never project files
```

A command function should read like: parse → call one service function →
render result. If a command has more than ~15 lines that aren't argument
handling, that logic belongs in `core/`.

## 3. Two run modes

- **Global**: `mycli --version`, `mycli auth login` — no project needed.
- **Project-aware**: `mycli status`, `mycli run` — walks up from cwd looking
  for `.{{package_name}}/`, or takes an explicit `--project PATH`.

This dual mode is what lets an agent `cd` into any directory and just run
the CLI, or point it at a project explicitly without changing cwd.

## 4. Project vs user vs secret storage — never mixed

| Data                     | Location                                   | Commit to git? |
|---------------------------|---------------------------------------------|----------------|
| Project config             | `<project>/.{{package_name}}/config.toml`  | Yes |
| Project state (generated)  | `<project>/.{{package_name}}/state.json`   | No |
| User-level config           | OS user config dir (`platformdirs`)        | N/A |
| Secrets                     | OS keychain via `keyring`, or env var       | Never |

Credential resolution order: CLI argument → environment variable → OS
keychain → (never falls back to project or global config for secrets).

### Credential shape: a named field-bag per `provider`, not one opaque string

`provider` is whatever identifies the credential in this CLI's domain — it
is not always "which API service." Three shapes come up in practice, and
all three go through the same `credentials/manager.py` storage, just with
different `provider` values and field sets:

- **One API key per service** (the default case): `provider="openai"`,
  fields `{"api_key": "..."}`. This is what `auth login/logout/status` and
  `get_secret`/`store_secret` handle out of the box.
- **Session/browser-style auth** (e.g. a tool automating a web app by
  replaying its cookies, the way `nlm`/NotebookLM-style CLIs do):
  `provider` names the target service, fields are whatever the session
  needs — `{"cookies": "...", "csrf_token": "...", "session_id": "..."}`.
  Use `get_credential`/`store_credential`/`read_fields_from_env` directly
  with an explicit `env_fields` list; don't force this through the
  single-secret wrappers.
- **Per-target credentials** (e.g. a site generator/deploy CLI that holds
  different credentials for each site it publishes to): `provider` is the
  target's own identifier (a hostname, a site slug), fields are whatever
  that target needs (`{"username": "...", "password": "..."}` or a deploy
  token). The project can have many such providers at once — `auth login
  --provider example.com` and `auth login --provider staging.example.com`
  are two independent, separately stored credentials.

A CLI can need more than one of these at once (e.g. one API key for an LLM
provider *and* per-site deploy credentials) — that's normal, not a
special case; each is just a different `provider` key in the same store.
Never invent a second storage mechanism for the "unusual" shape — extend
`credentials/manager.py`'s field-bag, don't bypass it.

## 5. AI-first output

Every command supports `--json`. Human output is for people at a terminal;
JSON output is the actual contract agents integrate against — see
`conventions.md` for the exact envelope. `--help` is also part of the API:
it must state exit codes and be safe for an agent to parse cold, with no
prior context.

A command function's docstring *is* its `--help` text (Typer renders it
directly), which makes it easy to edit a command's body and forget the
docstring is now stale. `scripts/check_command_docstrings.py`, installed as
a pre-commit hook by `scripts/install_hooks.sh`, warns (never blocks) when
that happens — `.git/hooks/` isn't versioned by git, so the install script
is what makes the hook survive a fresh clone.

## 6. Non-interactive by default for automation

Every command that could prompt (`init`, `auth login`, …) must accept
`--non-interactive` and fail with a clear `CliError` (not a hang) if it
can't get what it needs without prompting.

## 7. Cross-platform means Python APIs, not shell

`pathlib.Path`, `shutil`, `platformdirs` — never `os.system`, never
`subprocess.run(..., shell=True)`, never hardcoded POSIX paths. This is what
lets the exact same package install and run unmodified on macOS, Linux and
Windows.

## 8. Version compatibility

A project's `.{{package_name}}/config.toml` may declare
`[cli] min_version = "..."`. Prefer range checks (`>=1.2,<2.0`) over pinning
an exact CLI version — projects outlive any single CLI release.

## 9. Every package ships its own agent skill

`src/{{package_name}}/data/SKILL.md`, bundled into the installed package
(not just the source repo) so `<cli> --ai` and `<cli> skill install` can
serve it from anywhere. Describes discovery (`--help`, `status --json`,
`doctor --json`), installation, init, auth, output preference, error
inspection and — see below — which operations need explicit confirmation.

## 10. Safe vs. dangerous operations — confirm gate and dry-run

An agent that can run any command indiscriminately will eventually run a
destructive one it shouldn't have. Two mechanisms, both mandatory for any
command that changes external state irreversibly (deletes, overwrites a
remote resource, restarts a service, etc. — not for `init`/`config set`,
which only touch local project files):

- **`--dry-run`**: preview what the command would do without doing it.
  Check `output.is_dry_run(ctx)` first and short-circuit before any side
  effect.
- **`--confirm` / interactive confirmation**: call
  `output.require_confirmation(ctx, description, confirm)` immediately
  before the actual side effect (after any dry-run short-circuit, never
  before it). It prompts interactively when a human is at the terminal,
  and refuses with a clear `CliError` under `--non-interactive` unless
  `--confirm` was explicitly passed — an agent must never be able to
  trigger an irreversible action by accident just because it always adds
  `--non-interactive`.

The bundled `SKILL.md` must call out which commands are destructive and
tell the agent to always get explicit user sign-off before running them
non-interactively with `--confirm` — mirroring how a human would be asked.

## 11. Predictable, pipeable output

Output shape must not depend on whether stdout is a TTY or a pipe: no
interactive pagers (`less`, `click.echo_via_pager`), no prompts outside of
`require_confirmation`'s explicit gate, no output that only appears when a
human is watching. An agent piping a command's output must see exactly
what a human redirecting it to a file would see.

For a command that returns a list of records (not in the minimal
template, but common once one is added — e.g. `<cli> resource list`),
prefer **JSONL** (one JSON object per line) over a single large JSON array
under `--json`: it lets an agent start processing before the command
finishes and survives truncation better than a half-written array.
