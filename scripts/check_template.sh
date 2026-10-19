#!/bin/sh
# Template gate: run the repo tests, regenerate template/ for include_auth=true and false (default
# [tool.rb.install]), a publish-only variant (no homeserver users, no Mac) and adopt_core=true, prove
# copier update rounds from the previous release tag (defaults, and a flip to adopt_core=true),
# check the rendered [tool.rb.install], run the generated project's checks and its release gate
# (scripts/release.py, or rb-release from rb-cli-core with adopt_core). Non-zero exit on any failure.
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

# check_core_adopted: an adopt_core project has no copy of the gate, locks rb-cli-core from the
# gitea index and skips the tests of release.py with a reason naming rb-cli-core
check_core_adopted() {
    run test ! -e scripts/release.py
    run uv run python -c "import tomllib; p = tomllib.load(open('pyproject.toml', 'rb')); \
gitea = next(i['url'] for i in p['tool']['uv']['index'] if i['name'] == 'gitea'); \
core = [x for x in tomllib.load(open('uv.lock', 'rb'))['package'] if x['name'] == 'rb-cli-core']; \
assert [x['source'] for x in core] == [{'registry': gitea}], core"
    run uv run pytest -q --no-cov -p no:cacheprovider tests/test_scripts.py --junitxml="$WORK/$VARIANT-scripts.xml"
    run uv run python -c "import xml.etree.ElementTree as E; \
s = [e.get('message', '') for e in E.parse('$WORK/$VARIANT-scripts.xml').iter('skipped')]; \
assert s and all('rb-cli-core' in m for m in s), s"
}

# verify_project <expected (homeserver, mac) as a Python literal>: the checks of a generated
# project, run inside it; the gate is scripts/release.py, or rb-release when it answered adopt_core
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
    if grep -qx 'adopt_core: true' .copier-answers.yml; then
        check_core_adopted
        run uv run rb-release check
    else
        run test -e scripts/release.py
        run uv run python -c "import tomllib; p = tomllib.load(open('pyproject.toml', 'rb')); \
core = [d for d in p['project']['dependencies'] if d.startswith('rb-cli-core')]; \
assert not core and 'rb-cli-core' not in p['tool']['uv'].get('sources', {}), core"
        run uv run scripts/release.py --check
    fi
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

# check_update_round <name> [copier update --data args...]: generate from the previous release tag,
# update to the working tree with stdin closed and no credential variables, then run the full
# checks in the updated project.
check_update_round() {
    VARIANT=$1
    shift
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
        uvx copier update --trust --defaults -q --vcs-ref HEAD "$@" </dev/null
    verify_project '(["rbtools"], True)'
    cd "$ROOT"
}

VARIANT=repo-tests
run uv run --with pytest pytest -q "$ROOT/tests"

check_variant auth-true '(["rbtools"], True)' --data include_auth=true
check_variant auth-false '(["rbtools"], True)' --data include_auth=false
check_variant publish-only '([], False)' --data include_auth=true \
    --data install_homeserver_users= --data install_mac=false
check_variant core-true '(["rbtools"], True)' --data adopt_core=true
check_update_round update-round
check_update_round update-core-true --data adopt_core=true

printf '\nOK: template gate passed (repo tests, include_auth=true, include_auth=false, publish-only, adopt_core=true, update rounds)\n'
