#!/usr/bin/env python3
"""Cut a release: gate, assemble the changelog, commit, tag. Pushing is left to you.

    uv run scripts/release.py patch|minor|major

The version lives only in git tags (`vX.Y.Z`, read at build time by
uv-dynamic-versioning), so the next version is the last `v*` tag bumped by
`part`. Refuses off `main`, on a dirty tree, when `main` is behind its
upstream, when the gate fails, or when `changelog.d/` has no fragments.

Canonical copy: cli-generator `template/scripts/release.py`. Other repos
copy it verbatim instead of editing it — see tools/docs/standard-release.md §3.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

ROOT = Path(__file__).resolve().parent.parent
FRAGMENTS = ROOT / "changelog.d"
PARTS = ("patch", "minor", "major")
GATE = (
    ("uv", "run", "ruff", "check", "."),
    ("uv", "run", "ruff", "format", "--check", "."),
    ("uv", "run", "ty", "check"),
    ("uv", "run", "pytest"),
)
TAG_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")


def run(*args: str, capture: bool = False) -> str:
    result = subprocess.run(args, cwd=ROOT, check=True, text=True, capture_output=capture)
    return result.stdout.strip() if capture else ""


def fail(message: str) -> NoReturn:
    print(f"release: {message}", file=sys.stderr)
    raise SystemExit(1)


def check_branch() -> None:
    if run("git", "rev-parse", "--abbrev-ref", "HEAD", capture=True) != "main":
        fail("releases are cut from main")
    if run("git", "status", "--porcelain", capture=True):
        fail("working tree is not clean — commit or stash first")
    run("git", "fetch", "--quiet")
    try:
        counts = run("git", "rev-list", "--left-right", "--count", "HEAD...@{upstream}", capture=True)
    except subprocess.CalledProcessError:
        fail("main has no upstream — push it first (git push -u origin main)")
    _, behind = counts.split()
    if int(behind):
        fail(f"main is {behind} commit(s) behind its upstream — pull first")


def run_gate() -> None:
    for step in GATE:
        print("release: $", " ".join(step), flush=True)
        if subprocess.run(step, cwd=ROOT, check=False).returncode:
            fail(f"gate failed at: {' '.join(step)}")


def next_version(part: str) -> str:
    versions = [
        tuple(map(int, m.groups()))
        for t in run("git", "tag", "--list", "v*", capture=True).split()
        if (m := TAG_RE.match(t))
    ]
    if not versions:
        fail("no vX.Y.Z tag yet — tag the current version first: git tag -a v0.1.0 -m v0.1.0")
    major, minor, patch = max(versions)
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def main() -> None:
    part = sys.argv[1] if len(sys.argv) == 2 else ""
    if part not in PARTS:
        print(__doc__, file=sys.stderr)
        raise SystemExit(2)
    check_branch()
    if not [p for p in FRAGMENTS.glob("*") if not p.name.startswith(".")]:
        fail("changelog.d/ has no fragments — nothing to release (uv run towncrier create +<slug>.<type>.md -c '...')")
    version = next_version(part)
    tag = f"v{version}"
    if run("git", "tag", "--list", tag, capture=True):
        fail(f"tag {tag} already exists")
    run_gate()

    run("uv", "run", "towncrier", "build", "--version", version, "--yes")  # writes CHANGELOG.md, `git rm`s fragments
    run("git", "add", "--all", "CHANGELOG.md", *(["changelog.d"] if FRAGMENTS.exists() else []))
    run("git", "commit", "-m", f"Release {tag}")
    run("git", "tag", "-a", tag, "-m", tag)
    print(f"Released {tag} locally. Push it (needs your confirmation): git push --follow-tags")
    print(f'Then pin it anywhere with: uv tool install "git+<repo-url>@{tag}"')


if __name__ == "__main__":
    main()
