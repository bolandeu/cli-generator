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

### Distribution: develop locally, store in Gitea, install from the GitHub mirror — no PyPI required

The intended lifecycle is: develop on one machine, push to a Gitea repo
(`https://homeserver.tailee01ab.ts.net:3000/bolandeu/<name>`, the primary
store), and install that exact package on any other machine (any OS)
straight from its private GitHub mirror `bolandeu/<name>` (Gitea syncs all
refs, tags included; nobody pushes to GitHub):

```bash
uv tool install "git+https://github.com/<owner>/<repo>.git"
```

No PyPI publish step is needed for this to work — `uv tool install`
resolves and builds directly from the git URL. Pin a release by appending
`@vX.Y.Z` (a tag cut by `antagor publish`, see §8). This is wired into every generated package
automatically: the `repository_url` copier question fills in this exact
command in both `README.md` (for the human) and
`src/{{ package_name }}/data/SKILL.md` (for an agent that finds the skill
installed on a machine before the CLI binary itself is — e.g. a synced
`~/.claude/skills/` directory reaching a fresh machine ahead of the tool).
If `repository_url` was left blank at generation time, both files carry a
`<owner>/<repo>` placeholder to fill in once the repo exists.

The repo is **private by default**. These CLIs usually wrap one person's
accounts and providers, and nothing about the install path needs a public
repo: `uv tool install` shells out to git, so it authenticates exactly like
`git clone` does — over HTTPS through the credential helper that
`gh auth login` configures (`gh auth setup-git` if `gh` was logged in
non-interactively), or over SSH with the
`git+ssh://git@github.com/<owner>/<repo>.git` form. Both the generated
README.md and SKILL.md say this, so a fresh machine or an agent in a
sandbox knows what to do when the plain HTTPS install is refused with an
auth error. Later updates on any machine are `uv tool upgrade <pkg>`.

Creating that repo is part of the skill's job (SKILL.md, "Publish"):
after the package verifies, it prepares the local repo, runs `git init`,
`git remote add origin` and the first `git push -u origin main` to Gitea
itself (allowed on repo init without asking); until Gitea push-to-create
is live, the Human first creates the repo with sysadmin's
`scripts/new-repo-in-gitea.sh <name> --from <path>`. Then the skill proves
the from-mirror install works — in both Scaffold and Refactor mode.

## 2. Four layers

```
CLI (commands/)      — argument parsing, --json/--help, nothing else
  ↓
Core (core/)         — services, models, errors: the real business logic
  ↓
Providers / Filesystem / Credentials
  — providers/    external APIs, LLMs, etc. (subclasses of HttpProvider)
  — core/services  project filesystem state (.{{package}}/config.toml)
  — credentials/   OS keychain + env vars, never project files
```

A command function should read like: parse → call one service function →
render result. If a command has more than ~15 lines that aren't argument
handling, that logic belongs in `core/`.

### Providers: one `HttpProvider` subclass per external service

`providers/http.py` is the base for anything that speaks HTTP. A subclass
sets `name` and `base_url`, overrides `auth_headers()` (reading the secret
from `credentials.manager`, never from config) and adds typed methods that
call `self.request(...)` / `self.get_json(...)`. The base already does
what every integration otherwise reinvents slightly differently:

- 401/403 → `AuthRequired` (exit 3, `action` names the login command)
- 429 / 502 / 503 / 504, timeouts and connection errors → retried with
  exponential backoff (honoring `Retry-After`), then `ProviderError` (exit 5)
- other 4xx/5xx → `ProviderError` with the HTTP `status` in the envelope
- a non-JSON body from `get_json` → `ProviderError`
- a `User-Agent` of `<cli>/<version>` and a 30 s timeout, so a stuck
  service can't hang an agent forever

`transport` is a test seam for `httpx.MockTransport` — the template's
`tests/test_providers.py` shows the pattern.

**Every provider implements `health_check()`.** `HttpProvider` extends
`providers.base.Provider`, which declares `name`, `credential_fields`
(the field names it reads from `credentials.manager`; default
`("api_key",)`, `()` for none), `required` (`False` for a provider the
CLI works without), `legacy_env` (older env var names still honoured,
field → name, looked up **after the keychain** unless `legacy_env_first`;
annotate it `ClassVar[dict[str, str]]` in a subclass), `shared_namespaces`
(other CLIs whose stored credential this provider may read, after its
own: `("serp",)` for a tool using serp's key — read-only), and
`health_check() -> Health`:
one cheap, read-only, non-billed call proving the credential works, within
10 s and without retries, guaranteed by the provider's **own client
timeout** (no watchdog thread — it can't be killed and blocks interpreter
exit): for HTTP, `self.probe("/me")` makes exactly one request with a 10 s
httpx timeout; a non-HTTP provider passes `credentials.health.CHECK_TIMEOUT`
to what it calls; then `return Health(expires_at=..., quota=...)`; let
`AuthRequired`/`ProviderError` propagate. `auth status` gets the instance
from `for_health_check(target)` (`cls()` by default — override it when the
constructor needs config) and knows nothing about HTTP. `providers.all_providers()` finds every concrete subclass
defined under `providers/` by itself (no registry to forget; bases set
`abstract = True`), and `tests/test_providers.py` fails for any that
doesn't override `health_check()`. This is what `auth status --check`
runs (§4, "`auth status`").

Non-HTTP integrations (a vendor SDK, a local binary, a database driver)
still live under `providers/` and still speak the same error language,
subclassing `Provider` directly. The contract is the same mappings, done
at the provider boundary so nothing above it ever sees a vendor
exception:

```python
# providers/ffmpeg.py — sketch, not in the template
class FfmpegProvider(Provider):
    name = "ffmpeg"
    credential_fields = ()  # no credential: not listed by `auth status`

    def health_check(self) -> Health:
        return Health() if shutil.which("ffmpeg") else Health("unreachable", message="ffmpeg not on PATH")

    def transcode(self, src: Path, dst: Path) -> None:
        exe = shutil.which("ffmpeg")
        if exe is None:  # "not installed" is a provider failure with a fix
            raise ProviderError(self.name, "ffmpeg not found on PATH", action="Install ffmpeg and retry.")
        result = subprocess.run([exe, "-i", str(src), str(dst)], capture_output=True, text=True)
        if result.returncode != 0:  # vendor failure → ProviderError, never a traceback
            raise ProviderError(self.name, result.stderr.strip()[-200:])

# A vendor SDK: wrap its exceptions the same way — its auth error →
# AuthRequired(self.name); its rate-limit/outage errors → ProviderError(...,
# action="Retry later."); anything else it raises → ProviderError with the
# message. Retry only if the SDK doesn't already.
```

Test such a provider by injecting the thing it calls (`subprocess.run`,
the SDK client) exactly like `transport` on `HttpProvider`.

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
| Tool data (records, history) | shared PostgreSQL (`<TOOL>_DATABASE_URL`), else SQLite in the user data dir — §12 | Never |

Credential resolution order: CLI argument → environment variable → OS
keychain → legacy env var name if the provider declares one (never falls
back to project or global config for secrets).

**Namespace = the command name** (`cli_name`), not the Python package:
keychain service `<cli>:<provider>`, env var `<CLI>_<PROVIDER>_<FIELD>` with
every non-alphanumeric → `_` (`serp` → `SERP_XMLRIVER_API_KEY`, even though
the package is `rb_serp`; `sitemap-xml` → `SITEMAP_XML_…`). That's what a
user knows, and it stays put if the package is renamed. A provider reads
another tool's namespace via `shared_namespaces` and uses
`Provider.credential()`, which applies all of these options — so no
project needs its own copy of `credentials/manager.py` or `health.py`.

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

### `auth status` — the credentials health contract

`<cli> auth status [--check] [--provider NAME] --json` exists in **every**
CLI — one generated with `include_auth=false` reports `credentials: []`
and exits 0 (no `login`/`logout` there) — and reports every
provider with credentials in one fixed shape (shared across all our tools;
`tools-watch` reads it without
knowing any provider):

```json
{"ok": true, "tool": "serp", "version": "0.3.0", "checked_at": "2026-09-27T12:00:00Z",
 "credentials": [{"provider": "xmlriver", "required": true, "fields": ["user", "token"],
   "source": "env", "source_ref": "SERP_XMLRIVER_USER, SERP_XMLRIVER_TOKEN", "status": "ok",
   "expires_at": null, "quota": {"remaining": 1840, "limit": null, "unit": "requests"}, "message": null}]}
```

- `source`: `env` | `keychain` | `file` | `missing`; `source_ref` names env
  vars / keychain service / file — **never a value** (messages are scrubbed
  of credential values too). Env overriding part of a keychain credential
  reports `env` with both places in `source_ref`.
- `status`: `missing` / `unchecked` without `--check`; with it, the
  provider's `health_check()` (10 s client timeout, no retries) gives `ok`,
  or `AuthRequired` → `invalid`, `ProviderError`/timeout → `unreachable`,
  a past `expires_at` → `expired`, and the provider may return
  `quota_exhausted` itself.
- Exit `0` when every required provider is `ok`/`unchecked` (an optional
  one may be `missing`/`unreachable`); `3` when a required one has any
  other status or any credential is `invalid`/`expired`; `2` usage error.
  On `3` the envelope is `ok: false` + `error.code: CREDENTIALS_UNHEALTHY`
  **plus** the full report — a report is data even when it finds problems.
- **Per-target providers** (`per_target = True`, e.g. `name = "deploy"`):
  one credential per site/host/account stored as `<kind>:<target>`
  (`auth login --provider deploy:example.com`), and one report entry per
  stored target, `provider: "deploy:example.com"`, each checked with its
  own credential (`self.credential_name` in `auth_headers()`; `auth status`
  sets `self.target`). Targets are listed from an index the credential
  manager keeps in the keychain (keyring can't enumerate); an env-only
  target is reported when asked for by name (`--provider deploy:x.com`;
  env var `<CLI>_DEPLOY_X_COM_API_KEY` — non-alphanumerics become `_`).
  No stored target → one `deploy` entry, `missing`.
- The shape is pinned by `tests/test_auth.py`; changing it is a breaking
  change (§8, SemVer). Implementation: `credentials/health.py`.

## 5. AI-first output

Every command supports `--json`. Human output is for people at a terminal;
JSON output is the actual contract agents integrate against — see
`conventions.md` for the exact envelope. `--help` is also part of the API:
it must state exit codes and be safe for an agent to parse cold, with no
prior context — which is also why a bare `<cli>` or `<cli> <group>` prints
help and exits 0 instead of a usage error, with `<name> <version> —
<description>` as the header so one call answers "what is this and what
can it do".

That contract holds even when something goes wrong that nobody planned
for: `output.guard` wraps every command, so an escaped exception becomes
an `UNEXPECTED` JSON envelope (exit 1) rather than a traceback where an
agent expected JSON. Diagnostics never share stdout with data: human
errors, `--verbose` progress and `logging` all go to stderr
(`output.configure_logging` turns `--verbose` into DEBUG-level logging,
which is where a provider's request/retry lines show up).

A command function's docstring *is* its `--help` text (Typer renders it
directly), together with each parameter's `help=`. That help is the
documentation agents and humans read, so it must always match the code.
**Rule: change a command's behaviour → update its docstring in the same
commit.** Enforced at three deterministic levels, one shared check
(`scripts/check_command_docstrings.py`: a command is a function in
`src/*/commands/*.py` decorated with `output.guard`; its "logic" is its
signature + body without the docstring, compared with `HEAD`):

1. **The ticket check** `scripts/check_command_docstrings.py` (listed in
   `checks` of `.agents/antagor/antagor.toml`, so Antagor runs it on every
   ticket). It exits non-zero when a command's logic changed and its
   docstring did not. There are no hand-made Claude Code hooks.
2. **Blocking tests in the gate** (`tests/test_help.py`), walking the
   app's command registry so a new command is covered automatically:
   every command has a docstring with an `Example: <cli> <command> ...`
   line, every `typer.Option`/`Argument` has non-empty `help=`, every
   group has a description.
3. **Help snapshots**: `<command> --help` for every command and group is
   stored in `tests/snapshots/help/<command>.txt` (syrupy, fixed 100-column
   rendering). Any help change fails until
   `uv run pytest --snapshot-update` rewrites the file, so the new text
   is in the diff reviewers see; a missing or orphaned snapshot fails too.
   Snapshots contain the CLI's name, so copier renders them at `copier
   copy` time (`_tasks`) instead of shipping them.

The project keeps no `.githooks/` and sets no `core.hooksPath`: Antagor's
git hooks (`antagor hooks install`) only work without it. For a change that
truly doesn't alter behaviour an **agent** keeps the command body
AST-identical — a lint/type fix goes in as a `# noqa` / `# ty: ignore[...]`
comment, which doesn't change the AST — instead of the
`SKIP_DOCSTRING_CHECK=1 git commit ...` escape; that one is for humans (an
auto-mode classifier rightly blocks it as a bypass). A command is any
function decorated with `output.guard` or registered with
`@<app>.command(...)`, and `tests/test_help.py` requires every registered
command to be wrapped in `output.guard` (JSON error envelope, local
`--json`, the `{cli}` substitution).

Write `{cli}` for the CLI's name in docstrings (`Example: {cli} status
--json`): `output.guard` substitutes it, so commands stay plain `.py`
files that survive a rename. syrupy over inline-snapshot: help pages are
long multi-line text best reviewed as one file per command, which is
syrupy's single-file extension; inline-snapshot keeps values inside the
test source, and its external files are hash-named.

## 6. Non-interactive by default for automation

Every command that could prompt (`init`, `auth login`, …) must accept
`--non-interactive` and fail with a clear `CliError` (not a hang) if it
can't get what it needs without prompting.

Long commands (more than a couple of minutes: the gate, PostgreSQL tests,
a big import) are started by agents only through `scripts/run_detached.sh
<label> <command...>` and followed with `scripts/runs_status.sh` —
`scripts/detach.py`, standard library only: `subprocess.Popen(...,
start_new_session=True)` (macOS has no `setsid`) under a small supervisor
that records the exit code; pid, stdout log, stderr and exit code per
label in `<user state dir>/<cli>/runs/`. A command in the agent's own
shell dies when the turn is interrupted.

## 7. Cross-platform means Python APIs, not shell

`pathlib.Path`, `shutil`, `platformdirs` — never `os.system`, never
`subprocess.run(..., shell=True)`, never hardcoded POSIX paths. This is what
lets the exact same package install and run unmodified on macOS, Linux and
Windows.

## 8. Version compatibility and releases

A project's `.{{package_name}}/config.toml` declares
`[cli] min_version = "..."` — the oldest CLI release that understands
this project (its config fields, the commands its automation calls).
`services.load_config` enforces it: an older installed CLI fails with
`CLI_TOO_OLD` (exit 6, `action: uv tool upgrade <cli>`), and `doctor`
reports it as a `cli_compat` check instead of failing. It's a lower
bound, not a pin — projects outlive any single CLI release, and an
upgrade is always the fix. A bare source run (nothing installed, not even
editable) has no version and skips the check.

For `min_version` to mean anything, versions have to actually move — and
the rules for that are the shared release standard (this section is the
standard, the template implements it):

- **The version is the git tag.** `pyproject.toml` has no `version =`
  line: `dynamic = ["version"]` with `uv-dynamic-versioning` reads the
  latest `vX.Y.Z` tag at build time (no tag in reach → `0.0.0`, which
  `check_cli_compat` treats as a dev build and skips). Runtime code reads
  it with `importlib.metadata.version(...)` (`core/version.py`), never a
  hard-coded string. `[tool.uv] cache-keys` includes git commit + tags so
  `uv run` rebuilds when a tag moves. A new repo is tagged `v0.1.0` on its
  first commit.
- **The changelog is written by Antagor.** Nobody edits `CHANGELOG.md`
  and there are no fragments (no towncrier, no `changelog.d/`):
  `antagor publish` appends a section built from the titles of the
  published tickets. A user-visible change therefore needs a ticket with
  a title that says what changed for the user.
- **`scripts/release.py` is the authoritative gate.** `--check` runs it
  without releasing — agents run it before every commit, CI (optional)
  runs only this, `tools-watch` runs it too, and it is a
  ticket check in `antagor.toml`: `uv lock --check`, ruff check, ruff
  format --check, ty, pytest, `uv build` + install of the wheel into a throwaway venv where
  `<cli> --version` must equal the wheel's METADATA version and
  `<cli> --help` must work (a library without a console script: every
  top-level package imports and `importlib.metadata.version()` equals the
  built version), and `osv-scanner --lockfile=uv.lock` when
  osv-scanner is installed (skipped with a notice otherwise; `brew install
  osv-scanner`). The first failing step stops it, named, with its output,
  and a last line `release: code failed` (exit 1) — or `release: audit
  failed` (exit 3) when only the vulnerability audit failed, so
  `tools-watch` can tell "broken code" from "bump a dependency".
- **`antagor publish --bump patch|minor|major`** is the only way a version
  moves (`[publish] versioning = "semver"` in `.agents/antagor/antagor.toml`;
  default `patch`). It merges the accepted tickets, writes the changelog
  from their titles, creates the tag `vX.Y.Z` (a valid PEP 440 version)
  and runs `deploy_command` (`sh scripts/deploy.sh`: it pushes `main`
  with the tags to `origin`, Gitea). Only
  the Human runs it. An
  agent never pushes by hand. `scripts/release.py` has no bump mode any more; it is only the
  gate. The template's copy is canonical: every repo following the
  standard uses it verbatim.
- **CI is optional**: one `ubuntu-24.04` job on the lowest supported
  Python that installs osv-scanner and runs `release.py --check` —
  nothing else of its own. Delete the workflow to save Actions minutes;
  nothing depends on it.
- **Versions mean compatibility (SemVer).** Removing/renaming/changing
  anything public — Python API, CLI commands or flags, the `--json` shape,
  exit codes or error codes, the `auth status` report (`conventions.md`)
  — is a major bump; a new feature with old behaviour intact is minor; a
  fix is patch. While at `0.x` (Cargo convention): fixes **and**
  compatible features are patch, anything breaking is minor
  (`0.2 → 0.3`). Deprecate first (warning + a ticket titled `deprecate ...`),
  remove in the next breaking release. Tables: `conventions.md`.

A tag is what makes `uv tool install "git+<url>@v1.2.0"` reproducible on
another machine and what `--version` / `doctor` report; cut one whenever a
project's `min_version` needs to be able to refer to the change.

### Depending on another tool

A CLI that imports another of our packages pins it to a released tag and
allows compatible updates — never `branch = "main"`, never a bare git URL,
never a committed `path =`:

```toml
[project]
dependencies = ["yandex-oauth>=0.2,<0.3"]

[tool.uv.sources]
yandex-oauth = { git = "https://github.com/bolandeu/yandex-oauth", tag = "v0.2.1" }
```

- Working against an unreleased provider locally: `uv pip install -e
  ../<provider>` in your venv, uncommitted.
- Bumping the pin is one commit: `tag = "vNEW"` + `uv lock
  --upgrade-package <name>` + the full gate.
- **External (non-Python) dependencies are declared** in `pyproject.toml`
  `[[tool.rb.external]]` — `name`, `required`, optional `min_version`,
  `check` (version command, default `<name> --version`), `why` (standard
  §12). The gate checks the list against `src/` both ways (every program
  run by a literal name — `require_cli("x")`, `shutil.which("x")`,
  `subprocess.run(["x", …])`, `npx` — is declared, every declared one is
  run — except an entry with `detect = false`, for a program run in a way
  the scan can't see: an injected runner, an absolute path; it still needs
  `why`). For one of our CLIs, `dist` (default `rb-<name>`) and `url` make
  `DEPENDENCY_TOO_OLD` print a runnable `uv tool install "<dist> @
  git+<url>.git@v<min>" --force`. `doctor` shows an `external:<name>` check per entry; the wheel
  carries `pyproject.toml` as `<package>/_pyproject.toml` so the installed
  tool can read it.
- A CLI that shells out to another CLI (not imports it) declares the
  minimum version it needs and checks it at runtime before the first
  call: `exe = core.deps.require_cli("serp", "0.3.0",
  install_url="https://github.com/bolandeu/serp")`, then run `exe`. With
  `install_url` a missing CLI's `action` is a runnable
  `uv tool install --reinstall "git+<url>@v0.3.0"`; without it the action
  names what to install, never a `<…>` placeholder.
  A missing or older CLI fails with `DEPENDENCY_TOO_OLD` (exit 1: what's
  installed, what's needed, the `uv tool upgrade` command) instead of a
  confusing downstream error; a `0.0.0…` dev build is accepted.

## 9. Every package ships its own agent skill

`src/{{package_name}}/data/SKILL.md`, bundled into the installed package
(not just the source repo) so `<cli> --ai` and `<cli> skill install` can
serve it from anywhere. It is **conventions only** — install command,
`--json`, exit codes, credential rules, the dry-run/confirm gate — and
deliberately never lists commands: a bare `<cli>` prints name, version,
description and every command with the first line of its docstring, and
`<cli> <command> --help` the rest. Listing commands in the skill would
duplicate that into an agent's context and go stale the first time a
command is added; the docstrings can't go stale because they *are* the
help. Consequence: adding a command means writing a good docstring, not
editing SKILL.md.

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
what a human redirecting it to a file would see — and never an error
message mixed into it (those go to stderr, see `conventions.md`).

For a command that returns a list of records (not in the minimal
template, but common once one is added — e.g. `<cli> resource list`),
prefer **JSONL** (one JSON object per line) over a single large JSON array
under `--json`: it lets an agent start processing before the command
finishes and survives truncation better than a half-written array.

## 12. Tool data: the shared database (`include_db`)

A tool that keeps data (journals, results, history, caches) generates with
`include_db=true`: `core/db.py` (connection, revision check, upgrade,
import), `core/tables.py` (SQLAlchemy Core tables), `migrations/`
(Alembic), `commands/db.py`, `core/normalize.py`. SQLAlchemy Core +
Alembic + psycopg 3 — no ORM, no hand-rolled migrations. All of a
tool's data goes through this layer by default, caches included (a shared
cache of paid API responses is the point: Mac and homeserver don't pay
twice). Keeping something local instead is the tool's decision, recorded
with its reason in the tool's own `AGENTS.md` (serp and wordstat keep
their response caches in PostgreSQL; llmkit keeps its response cache in
local SQLite and only its spend log in PostgreSQL).

**Where.** `<TOOL>_DATABASE_URL` set → PostgreSQL (the shared base on the
homeserver, the one Directus uses; the URL comes from Doppler). Set but
unreachable / rejected → `DATABASE_UNAVAILABLE`, exit 5 — **never** a
fallback to SQLite, whose rows would silently miss the shared base. Not
set → SQLite in the user data dir (tests, offline work), or at
`<TOOL>_DB_PATH` when that is set. `<TOOL>` is
`cli_name` with non-alphanumerics as `_` (`_distribution.TOOL`, written
down at generation, never derived at runtime).

**Names and ownership.** Everything lives in schema `public` (Directus
sees one schema), so every table, view, index and constraint starts with
`<tool>_`. A tool is the only owner of its objects: DDL only through its
own migrations, tracked in its own `alembic_version_<tool>` table.
Alembic is filtered to the prefix (`migrations/env.py`) — it never
reflects, compares or touches another tool's tables or Directus'.
`tables.py` mirrors the latest migration; `tests/test_db.py` fails when
they disagree. Every table has a **single-column** PRIMARY KEY — Directus
can't show or edit a table without one and doesn't support a composite
one: a surrogate `id`, the natural key as a UNIQUE constraint (the test
checks both the metadata and the migrated database). Every table says
what its rows are — `info={"kind": "data"}` (the tool's result, lost when
deleted) or `"cache"` (a copy it can fetch again); the test fails without
it. Which is which is the dev side's call, approved by the user. A
`cache` table lives in PostgreSQL schema `cache` (`schema=CACHE_SCHEMA`
in `tables.py`; the test checks kind and schema agree), the data in
`public`; on SQLite the engine maps the schema away (`schema_translate_map`)
— the same file as before. The `<tool>_v1_*` views stay in `public` and
read `cache.<table>`. The schema and the role's USAGE + CREATE on it are
the infrastructure's job: `db upgrade` checks both before any migration
runs and stops with `DATABASE_UNAVAILABLE` (nothing moved) when either is
missing. An existing table moves with one migration — `ALTER TABLE ...
SET SCHEMA cache` (rows, indexes, constraints and the id sequence go with
it, views follow), the template's `migrations/versions/0002_cache_schema.py.jinja`
is the pattern; a new tool creates its cache tables in `cache` from the
start. The template's revisions are seed examples: `copier update` never
touches `migrations/versions/` (`copier.yml` `_exclude`). Migrations are written by hand, with
literal names. Tests against PostgreSQL run only through
`scripts/pg_test.sh`: a throwaway container with its own name on a port
Docker assigns, removed afterwards — a fixed port once let one tool's
tests drop a table in another tool's test database.

**Contract between tools.** Another tool (or Directus, or a report)
reads only views named `<tool>_v1_*`, never the tables. A view's columns
don't change: a different shape is a new `<tool>_v2_*` view next to the
old one, plus a line in the root `AGENTS.md` Service map; `v1` is
dropped only after every consumer has moved. Views are created by a
migration (`CREATE VIEW`) and declared in `tables.py` `views` (a separate
`MetaData`: name, typed columns, `comment=` descriptions) — that declaration
is what `describe --json` publishes as the tool's data contract
(conventions.md), and `tests/test_db.py` fails when a declared view is
missing from the migrated database or its columns differ. Files the tool
keeps in its user data dir besides the SQLite file are declared in
`core/data_files.py` `DATA_FILES` for the same reason. Tools link records by
natural keys, not by each other's ids: `core/normalize.py`
(`norm_phrase` — NFKC, lower, ё→е, collapsed whitespace — with the
region as a second key column; `norm_url`, `norm_domain` — no scheme,
`www.`, port or trailing slash, IDN as Unicode). Store the key in its own
indexed column (`phrase_key`) next to the original text (`phrase`); the
key loses information, the original must not. Changing a normalization
is a new view version and a migration that recomputes the key.

**Migrations.** SQLite is migrated on open. PostgreSQL is one database
for every machine — a dev checkout must not migrate it — so it is never
migrated implicitly: `<cli> db upgrade` (released version, under a
`pg_advisory_xact_lock`, one transaction). Opening it only compares
revisions: behind → `DATABASE_NOT_MIGRATED` (exit 1, "run db upgrade");
at a revision this release doesn't know → `CLI_TOO_OLD` (exit 6, "upgrade
the tool"). Nothing is touched in either case. Because the previous
release keeps running against the upgraded base until every machine
updates, **every migration must work with the previous release's code
(expand/contract)**: add a column/table/view first (nullable or with a
default), switch the code in that release, and drop or rename the old
thing only in a later release, after nothing reads it. A rename is
add + copy + later drop, never `ALTER ... RENAME` of something the
previous release uses.

**Commands.** `db status` (where, current vs head revision), `db upgrade
[--dry-run]`, `db import-sqlite [PATH] [--dry-run]` — the one-off move of
the local SQLite (default: the tool's own file, migrated to head first)
into the configured database: all tables, one transaction, every target
table must be empty, sequences moved past the imported ids. `doctor`
reports `database` (connection) and `database_schema` (revision).

**Dev → prod: `db push`.** A dev machine works on its local SQLite;
production is the PostgreSQL in `<TOOL>_PROD_DATABASE_URL` (Doppler). `db push [--table T] [--since DATE] [--where SQL]
[--dry-run]` sends the local rows of the *push tables* there: tables
marked `info={"push": {"since": "<timestamp column>"}}` in `tables.py` —
append-only, with a unique constraint on the natural key and no foreign
keys. Rows go in without their ids (`INSERT … ON CONFLICT DO NOTHING`):
one whose key is already in prod is skipped, so a repeated push is
harmless. Production's revision is checked first, as on open (behind →
`DATABASE_NOT_MIGRATED`, newer → `CLI_TOO_OLD`). One transaction;
`--dry-run` rolls it back, so its counts (`selected`, `sent`, `skipped`
per table) are exact. A table that is updated in place is not a push
table. An agent never runs anything against production —
`db push` (dry run included), reads through `<TOOL>_PROD_DATABASE_URL`,
ssh to the server; it gives the Human the exact command.


## 13. Consumer contracts

What other tools, Windmill flows, the Astro build and the platform rely on in
a CLI is pinned by **their** tests, run by **its** gate (consumer-driven
contracts). The consumer writes the contract
(the source of truth is the consumer's repo, the tool keeps a copy, both
through the Human); the tool's agent never edits it to pass — a contract that
changed or vanished shows up in the gate's `existing tests` list. The format
is the consumers'; a change to it goes to the Human with a reason.

**Where.** `tests/contracts/<consumer>/<provider>.yaml` (e.g.
`tests/contracts/windmill/serp.yaml`), format `contract: 1` in
`tests/contracts/schema.json` (`$defs/contract`), validated before anything
runs — a broken file fails naming itself, a contract for another provider
too. Runner: `tests/test_contracts.py`, one test per check, id
`<consumer>:<section>:<name>`.

```yaml
contract: 1
consumer: windmill
provider: serp
provider_range: ">=0.6,<1.0"     # outside it the contract doesn't apply
contact: "windmill's agent, through dev"
static:                          # against `describe --json`
  commands:
    - path: [search]
      arguments: [queries]
      options: [--engine, --json]
  root_options: [--version]
  exit_codes: [0, 1, 2, 3, 5]    # each must be in exitCodes
  env: [SERP_XMLRIVER_USER]      # each must be in x-rb-env (name or fallback)
run:                             # the CLI in-process, offline
  - name: search_json_envelope
    argv: [search, "{fixture_query}", --cache, --json]
    exit: 0
    stdout_json_schema: {type: object, required: [ok, count, results]}
  - name: auth_missing_is_exit_3
    argv: [search, "{fixture_query}", --provider, xmlriver, --json]
    env_unset: [SERP_XMLRIVER_USER]
    offline_cache: false         # no cache: must fail before the provider
    exit: 3
  - name: version
    argv: [--version]
    exit: 0
    stdout_regex: '^\d+\.\d+\.\d+'
view:                            # describe --json and the migrated test database
  - name: serp_v1_responses
    columns: {phrase_key: text, region: integer, fetched_at: datetime}
```

- `static` — commands (path, positional arguments, options by name or
  alias), root options, documented exit codes, env var names.
- `run` — every run is **offline and keyless**: DNS and connections to
  anything but loopback are refused *and recorded* — a case that tried the
  network fails even when the CLI caught the error and exited "right" (it
  must not cost money); every `x-rb-env` variable is unset and the OS
  keychain disabled; then `env_unset`. `{placeholders}` in `argv` and the
  offline data come from the tool's own `tests/contracts/fixtures.yaml`
  (`$defs/fixtures`): `placeholders` (name → value), `offline_cache` (a
  pytest fixture in `tests/conftest.py` that puts recorded responses / a
  filled cache / fake keys in place) and `no_cache` (for `offline_cache:
  false` cases, which must fail before reaching the provider). An unknown
  placeholder or fixture fails the case naming it. The exit code must
  match; `stdout_json_schema` (extra fields are fine, a missing required one
  is not) or `stdout_regex` (re.search).
- `view` — columns and type families (`text`, `integer`, `number`,
  `boolean`, `date`, `datetime`, `json`, `any`; VARCHAR is text, BIGINT
  integer, TIMESTAMP WITH TIME ZONE datetime) in `describe --json` and on
  the migrated test database: SQLite, PostgreSQL too under
  `scripts/pg_test.sh`.
- `provider_range` — PEP 440. The gate passes the version being released,
  so `<1.0` stops applying in the release that makes 1.0.0.

**Gate.** `release.py --check` runs the contracts as their own step, apart
from pytest: `contracts ... ok (N cases from K consumers)`; a failure
prints each failing `<consumer>:<section>:<name>` with what exactly is
wrong, and the release doesn't go out. Every template ships one real
contract: `tests/contracts/tools-catalog/<cli>.yaml` — the tools catalog
reads `describe --json`.
