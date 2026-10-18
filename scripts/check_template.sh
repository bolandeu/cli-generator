#!/bin/sh
# Template gate: regenerate template/ for include_auth=true and false, run the
# generated project's checks and its release gate. Non-zero exit on any failure.
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

check_variant() {
    VARIANT=$1
    dest="$WORK/$VARIANT"
    run uvx copier copy "$ROOT" "$dest" \
        --data package_name=demotool --data project_name=Demo \
        --data description=d --data author_name=A --data "include_auth=${2}" \
        --data "install_homeserver_users=${3-rbtools}" --data "install_mac=${4-true}" \
        --defaults --trust -q --vcs-ref HEAD
    cd "$dest"
    run uv sync -q
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

check_variant auth-true true
check_variant auth-false false
check_variant publish-only true "" false

printf '\nOK: template gate passed (include_auth=true, include_auth=false, publish-only)\n'
