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
resolves and builds directly from the git URL. Pin a release by appending
`@vX.Y.Z` (a tag cut by `scripts/release.py`, see §8). This is wired into every generated package
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

Creating that repo is part of the skill's job (SKILL.md, "Publish to
GitHub"): after the package verifies, it offers to `gh repo create
--private --source=. --push` and then proves the from-GitHub install
works — in both Scaffold and Refactor mode, never without the user's
go-ahead.

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
provider with credentials in one fixed shape (shared across all our tools,
`tools/docs/standard-release.md` §8; `tools-watch` reads it without
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

1. **Claude Code hooks** (`.claude/settings.json`, versioned). PostToolUse
   on `Edit|Write|MultiEdit` of a command file exits 2 with "update the
   docstring of command X" when its logic changed and its docstring did
   not; the Stop hook refuses to end the turn while any command in the
   working tree is in that state (once per turn — `stop_hook_active`
   lets the second attempt through, so a genuinely behaviour-neutral
   refactor can't loop). SessionStart points git at `.githooks/`.
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

Plus the git pre-commit hook in `.githooks/pre-commit` (versioned; active
after `scripts/install_hooks.sh`, which sets `core.hooksPath`) runs the
same check on the staged files and blocks the commit; for a change that
truly doesn't alter behaviour: `SKIP_DOCSTRING_CHECK=1 git commit ...`.

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
the rules for that are the shared release standard
(`~/Projects/tools/docs/standard-release.md`; this section is its summary,
the template implements it):

- **The version is the git tag.** `pyproject.toml` has no `version =`
  line: `dynamic = ["version"]` with `uv-dynamic-versioning` reads the
  latest `vX.Y.Z` tag at build time (no tag in reach → `0.0.0`, which
  `check_cli_compat` treats as a dev build and skips). Runtime code reads
  it with `importlib.metadata.version(...)` (`core/version.py`), never a
  hard-coded string. `[tool.uv] cache-keys` includes git commit + tags so
  `uv run` rebuilds when a tag moves. A new repo is tagged `v0.1.0` on its
  first commit.
- **The changelog is assembled from fragments.** Nobody edits
  `CHANGELOG.md` between releases — every user-visible change adds
  `changelog.d/+<slug>.<type>.md` (`uv run towncrier create +<slug>.<type>.md
  -c "..."`; type = added/changed/deprecated/removed/fixed/security). Two
  branches never touch the same line, so they never conflict. The gate
  (below) requires one whenever something user-visible changed since the
  last tag — tooling-only changes (`uv.lock`, `.github/`, `scripts/`,
  `tests/`, `.githooks/`, `.claude/`, `AGENTS.md`, `CLAUDE.md`) need none,
  so the changelog stays about the package; the pre-commit hook
  (`scripts/check_changelog_fragment.py`) warns locally, never blocks.
- **`scripts/release.py` is the authoritative gate.** `--check` runs it
  without releasing — agents run it before every commit, CI (optional)
  runs only this, the root agent's `tools-watch` runs it too: `uv lock
  --check`, ruff check, ruff format --check, ty, pytest, a changelog
  fragment present whenever anything user-visible changed since the last
  tag (checked in the working tree — `towncrier check` only sees commits;
  the tooling-only paths above need none — `NO_FRAGMENT_NEEDED`, the same
  list in `release.py` and `check_changelog_fragment.py`, pinned by
  `tests/test_scripts.py`),
  `uv build` + install of the wheel into a throwaway venv where
  `<cli> --version` must equal the wheel's METADATA version and
  `<cli> --help` must work (a library without a console script: every
  top-level package imports and `importlib.metadata.version()` equals the
  built version), and `osv-scanner --lockfile=uv.lock` when
  osv-scanner is installed (skipped with a notice otherwise; `brew install
  osv-scanner`). The first failing step stops it, named, with its output.
- **`release.py patch|minor|major`** is the only way a version moves: on a
  clean `main` not behind its upstream, it runs the same gate (building
  the wheel as the new version via `UV_DYNAMIC_VERSIONING_BYPASS`, since
  the tag doesn't exist yet), bumps the last `v*` tag, runs
  `towncrier build`, commits `Release vX.Y.Z` and creates the annotated
  tag. It does **not** push — it prints `git push --follow-tags`, which
  the user confirms. The template's copy is canonical: every repo
  following the standard uses it verbatim.
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
  (`0.2 → 0.3`). Deprecate first (warning + a `deprecated` fragment),
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
