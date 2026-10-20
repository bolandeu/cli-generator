#!/bin/sh
# Template gate: run the repo tests and the tests of gate/, regenerate template/ for include_auth=true
# and false (default [tool.rb.install]), a publish-only variant (no homeserver users, no Mac) and
# include_db=true, prove copier update rounds from the previous release tag and from v1.20.10 (the
# last template that copied the gate, with adopt_core false and true), check the rendered [tool.rb.install], run the generated project's checks and the
# release gate from this working tree's gate/ through uvx. Non-zero exit on any failure.
# Usage: sh scripts/check_template.sh
set -eu

ROOT=$(cd "$(dirname "$0")/.." && pwd)
WORK=$(mktemp -d "${TMPDIR:-/tmp}/cli-gen-check.XXXXXX")
trap 'rm -rf "$WORK"' EXIT INT TERM

step() { printf '\n==> [%s] %s\n' "$VARIANT" "$*"; }

run() {
    step "$*"
    "$@" || { printf '\nFAILED [%s]: %s\n' "$VARIANT" "$*" >&2; exit 1; }
}

command -v antagor >/dev/null 2>&1 || {
    printf '\nFAILED: antagor не найден в PATH: нужен для antagor layout check\n' >&2
    exit 1
}

# The last template version that copied the gate into scripts/release.py (adopt_core false) or took
# it from rb-cli-core (adopt_core true).
GATE_COPY_TAG=v1.20.10
STANDARD=https://homeserver.tailee01ab.ts.net:3000/bolandeu/cli-generator/src/branch/main/skills/cli-builder/reference/standard.md

fail() { printf '\nFAILED [%s]: %s\n' "$VARIANT" "$*" >&2; exit 1; }

# check_gate_files [README.md]: the project has no copy of the gate, no adopt_core answer and no
# rb-cli-core in any tracked file; its CI, antagor.toml, AGENTS.md (and README.md when named) call
# the uvx gate at the template tag of .copier-answers.yml; AGENTS.md and the package skill link the
# Standard and cite no § numbers
check_gate_files() {
    run test ! -e scripts/release.py
    grep -q adopt_core .copier-answers.yml && fail "adopt_core in .copier-answers.yml"
    git grep -q rb-cli-core && fail "rb-cli-core in $(git grep -l rb-cli-core | tr '\n' ' ')"
    tag=$(sed -n 's/^_commit: //p' .copier-answers.yml)
    gate="uvx --from \"git+https://homeserver.tailee01ab.ts.net:3000/bolandeu/cli-generator.git@$tag#subdirectory=gate\" rb-release check"
    for file in .gitea/workflows/ci.yml .agents/antagor/antagor.toml AGENTS.md "$@"; do
        grep -qF "$gate" "$file" || fail "$file does not call: $gate"
    done
    for file in AGENTS.md src/demotool/data/SKILL.md; do
        grep -qF "$STANDARD" "$file" || fail "$file does not link the Standard"
        grep -q '§' "$file" && fail "$file cites a § number"
    done
    return 0
}

# run_gate: the gate from this working tree's gate/ through uvx; it changes neither pyproject.toml
# nor uv.lock. --no-cache: uvx reuses its cached build of a local directory even when the code changed
# (--refresh and --reinstall do not help, uv 0.10).
run_gate() {
    before=$(cat pyproject.toml uv.lock | shasum)
    run uvx --no-cache --from "$ROOT/gate" rb-release check
    [ "$(cat pyproject.toml uv.lock | shasum)" = "$before" ] || fail "the gate changed pyproject.toml or uv.lock"
}

# verify_project <expected (homeserver, mac) as a Python literal> [README.md]: the checks of a
# generated project, run inside it, then the gate
verify_project() {
    expected_install=$1
    shift
    dest=$PWD
    run uv sync -q
    run uv run python -c "import tomllib; i = tomllib.load(open('pyproject.toml', 'rb'))['tool']['rb']['install']; \
assert (i['homeserver'], i['mac']) == $expected_install, i"
    run uv run ruff check .
    run uv run ruff format --check .
    run uv run ty check
    run uv run pytest -q
    run git add -A
    run git -c user.name=gate -c user.email=gate@example.invalid commit -q -m i
    run git -c user.name=gate -c user.email=gate@example.invalid tag -a v0.1.0 -m v0.1.0
    check_gate_files "$@"
    run_gate
    run antagor -C "$dest" layout check
}

# check_variant <name> <expected (homeserver, mac) as a Python literal> [copier --data args...]
check_variant() {
    VARIANT=$1
    expected_install=$2
    shift 2
    dest="$WORK/$VARIANT"
    run uvx copier copy "$ROOT" "$dest" \
        --data package_name=demotool --data project_name=Demo \
        --data description=d --data author_name=A "$@" \
        --defaults --trust -q --vcs-ref HEAD
    cd "$dest"
    run git init -q
    verify_project "$expected_install" README.md
    cd "$ROOT"
}

# generate_at <name> <template tag> [copier copy --data args...]: a committed project generated from
# that tag in $WORK/<name>; the shell stays in it
generate_at() {
    VARIANT=$1
    from=$2
    shift 2
    dest="$WORK/$VARIANT"
    run uvx copier copy "$ROOT" "$dest" \
        --data package_name=demotool --data project_name=Demo \
        --data description=d --data author_name=A "$@" \
        --defaults --trust -q --vcs-ref "$from"
    cd "$dest"
    run git init -q
    run git add -A
    run git -c user.name=gate -c user.email=gate@example.invalid commit -q -m previous
}

# update_staged: update the project in the cwd to the working tree through the worker script
# (stdin closed, no credential variables)
update_staged() {
    run env -u GH_TOKEN -u GITHUB_TOKEN -u GITHUB_READ_TOKEN -u GITEA_TOKEN -u DOPPLER_TOKEN \
        uvx --from copier python "$ROOT/skills/cli-builder/scripts/copier_update_staged.py" \
        --trust --defaults -q --vcs-ref HEAD </dev/null
}

# check_update_round <name> <template tag> [copier copy --data args...]: with CLEAN_TREE=1 the staged
# change is skipped and the script runs on a clean, committed tree. Generate from that tag, make a
# staged, uncommitted change, update to the working tree through the worker script, check the
# change survived, then run the full checks in the updated project.
check_update_round() {
    generate_at "$@"
    if [ -z "${CLEAN_TREE:-}" ]; then
        # The change a worker that may not commit holds: `_src_path` written another way (a trailing slash).
        run sed -i.bak -E 's|^(_src_path: .*[^/])$|\1/|' .copier-answers.yml
        run rm .copier-answers.yml.bak
        grep -qE '^_src_path: .*/$' .copier-answers.yml || { printf '\nFAILED [%s]: gate edit missing\n' "$VARIANT" >&2; exit 1; }
    fi
    update_staged
    if [ -z "${CLEAN_TREE:-}" ]; then
        grep -qE '^_src_path: .*/$' .copier-answers.yml || { printf '\nFAILED [%s]: staged change lost\n' "$VARIANT" >&2; exit 1; }
    fi
    # A template release that changes a help text or `describe` changes the snapshots: the project
    # refreshes them after an update (copier's task runs on copy only).
    run uv run --quiet pytest --snapshot-update --no-cov -q -p no:cacheprovider tests/test_help.py tests/test_describe.py
    verify_project '(["rbtools"], True)'
    cd "$ROOT"
}

VARIANT=repo-tests
run uv run --with pytest pytest -q "$ROOT/tests"
VARIANT=gate-tests
run uv run --directory "$ROOT/gate" ruff check .
run uv run --directory "$ROOT/gate" ruff format --check .
run uv run --directory "$ROOT/gate" ty check
run uv run --directory "$ROOT/gate" pytest -q

check_variant auth-true '(["rbtools"], True)' --data include_auth=true
check_variant auth-false '(["rbtools"], True)' --data include_auth=false \
    --data repository_url=https://homeserver.tailee01ab.ts.net:3000/bolandeu/demo
check_variant publish-only '([], False)' --data include_auth=true \
    --data install_homeserver_users= --data install_mac=false \
    --data repository_url=https://github.com/bolandeu/demo
check_variant db '(["rbtools"], True)' --data include_db=true
previous=$(git -C "$ROOT" tag --list 'v*' --sort=-v:refname | head -n 1)
[ -n "$previous" ] || { VARIANT=update-round; fail "no release tag to update from"; }
check_update_round update-round "$previous"
check_update_round update-from-copy "$GATE_COPY_TAG"
CLEAN_TREE=1 check_update_round update-from-core "$GATE_COPY_TAG" --data adopt_core=true

printf '\nOK: template gate passed (repo tests, gate tests, include_auth=true, include_auth=false, publish-only, include_db=true, update rounds)\n'
