#!/bin/sh
# Template gate: regenerate template/ for include_auth=true and false (default
# [tool.rb.install]) and a publish-only variant (no homeserver users, no Mac),
# check the rendered [tool.rb.install], run the generated project's checks and
# its release gate. Non-zero exit on any failure.
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
    run uv sync -q
    run uv run python -c "import tomllib; i = tomllib.load(open('pyproject.toml', 'rb'))['tool']['rb']['install']; \
assert (i['homeserver'], i['mac']) == $expected_install, i"
    run uv run ruff check .
    run uv run ruff format --check .
    run uv run ty check
    run uv run pytest -q
    run git init -q
    run git add -A
    run git -c user.name=gate -c user.email=gate@example.invalid commit -q -m i
    run git -c user.name=gate -c user.email=gate@example.invalid tag -a v0.1.0 -m v0.1.0
    run uv run scripts/release.py --check
    run antagor -C "$dest" layout check
    cd "$ROOT"
}

check_variant auth-true '(["rbtools"], True)' --data include_auth=true
check_variant auth-false '(["rbtools"], True)' --data include_auth=false
check_variant publish-only '([], False)' --data include_auth=true \
    --data install_homeserver_users= --data install_mac=false

printf '\nOK: template gate passed (include_auth=true, include_auth=false, publish-only)\n'
