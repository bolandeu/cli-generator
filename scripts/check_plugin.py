#!/usr/bin/env python3
"""Check the Claude Code plugin manifest and the skill frontmatter without the `claude` binary.

This is the part of `claude plugin validate . --strict` that this repo uses: the manifest's
required fields and its slug name, and the frontmatter of the bundled `cli-builder` skill.
Standard library only, so it runs as plain `python3 scripts/check_plugin.py` anywhere.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / ".claude-plugin" / "plugin.json"
SKILL = ROOT / "skills" / "cli-builder" / "SKILL.md"

REQUIRED_MANIFEST_KEYS = ("name", "description", "version")
REQUIRED_SKILL_KEYS = ("name", "description")
SLUG = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")


def frontmatter_lines(text):
    """The lines between the leading `---` and the closing `---`, or None if there is no such block."""
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return None
    for end, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return lines[1:end]
    return None


def frontmatter_fields(lines):
    """The top-level `key: value` pairs of a frontmatter block; indented (nested) keys are ignored."""
    fields = {}
    for line in lines:
        key, colon, value = line.partition(":")
        if colon and key == key.strip():
            fields[key] = value.strip()
    return fields


def check_manifest():
    """The parsed manifest and the messages of what is wrong with it."""
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except OSError as error:
        return {}, [f"{MANIFEST}: {error.strerror}"]
    except json.JSONDecodeError as error:
        return {}, [f"{MANIFEST}: not valid JSON: {error}"]
    if not isinstance(manifest, dict):
        return {}, [f"{MANIFEST}: not a JSON object"]
    problems = [f"{MANIFEST}: no {key!r}" for key in REQUIRED_MANIFEST_KEYS if key not in manifest]
    name = manifest.get("name")
    if "name" in manifest and not (isinstance(name, str) and SLUG.fullmatch(name)):
        problems.append(f"{MANIFEST}: name {name!r} is not a slug like [a-z0-9]+(-[a-z0-9]+)*")
    return manifest, problems


def check_skill():
    try:
        text = SKILL.read_text(encoding="utf-8")
    except OSError as error:
        return [f"{SKILL}: {error.strerror}"]
    lines = frontmatter_lines(text)
    if lines is None:
        return [f"{SKILL}: does not start with a --- frontmatter block"]
    fields = frontmatter_fields(lines)
    return [f"{SKILL}: frontmatter has no {key}" for key in REQUIRED_SKILL_KEYS if not fields.get(key)]


def main():
    manifest, problems = check_manifest()
    problems += check_skill()
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    print(f"plugin: {manifest['name']} v{manifest['version']}, skill cli-builder ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
