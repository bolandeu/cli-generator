#!/bin/sh
# Template gate: run the repo tests, regenerate template/ for include_auth=true and false (default
# [tool.rb.install]) and a publish-only variant (no homeserver users, no Mac), prove a
# copier update round from the previous release tag, check the rendered [tool.rb.install],
# run the generated project's checks and its release gate. Non-zero exit on any failure.
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

# verify_project <expected (homeserver, mac) as a Python literal>: the checks of a generated
# project, run inside it
verify_project() {
    expected_install=$1
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
    run uv run scripts/release.py --check
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
    verify_project "$expected_install"
    cd "$ROOT"
}

# check_update_round: generate from the previous release tag, update to the working tree with
# stdin closed and no credential variables, then run the full checks in the updated project.
check_update_round() {
    VARIANT=update-round
    previous=$(git -C "$ROOT" tag --list 'v*' --sort=-v:refname | head -n 1)
    [ -n "$previous" ] || { printf '\nFAILED [%s]: no release tag to update from\n' "$VARIANT" >&2; exit 1; }
    dest="$WORK/$VARIANT"
    run uvx copier copy "$ROOT" "$dest" \
        --data package_name=demotool --data project_name=Demo \
        --data description=d --data author_name=A \
        --defaults --trust -q --vcs-ref "$previous"
    cd "$dest"
    run git init -q
    run git add -A
    run git -c user.name=gate -c user.email=gate@example.invalid commit -q -m previous
    run env -u GH_TOKEN -u GITHUB_TOKEN -u GITHUB_READ_TOKEN -u GITEA_TOKEN -u DOPPLER_TOKEN \
        uvx copier update --trust --defaults -q --vcs-ref HEAD </dev/null
    verify_project '(["rbtools"], True)'
    cd "$ROOT"
}

VARIANT=repo-tests
run uv run --with pytest pytest -q "$ROOT/tests"

check_variant auth-true '(["rbtools"], True)' --data include_auth=true
check_variant auth-false '(["rbtools"], True)' --data include_auth=false
check_variant publish-only '([], False)' --data include_auth=true \
    --data install_homeserver_users= --data install_mac=false
check_update_round

printf '\nOK: template gate passed (repo tests, include_auth=true, include_auth=false, publish-only, update round)\n'
