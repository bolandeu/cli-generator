"""The Standard (skills/cli-builder/reference/standard.md): named sections, marked rules, no old reference files."""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STANDARD = ROOT / "skills" / "cli-builder" / "reference" / "standard.md"

SECTIONS = [
    "Technology",
    "Commands",
    "Output",
    "Errors",
    "Health",
    "Credentials",
    "Install",
    "Docs",
    "CI",
    "Release",
    "Optional parts",
]
OPTIONAL_PARTS = [
    "Project",
    "Credentials and providers",
    "HTTP",
    "Database",
    "Package skill",
    "Describe",
    "Consumer contracts",
    "Detach",
]
# The names `rb-release check` prints for its steps.
GATE_STEPS = {
    "standard: commands",
    "standard: json",
    "standard: errors",
    "standard: health",
    "standard: docs",
    "standard: ci",
    "secret scan",
    "uv lock --check",
    "ruff check",
    "ruff format --check",
    "ty check",
    "pytest",
    "contracts",
    "install section",
    "external dependencies",
    "build + install wheel",
    "vulnerability audit",
}
MANDATORY = re.compile(r"^- \*\*Mandatory\*\* \(gate: (?P<steps>`[^`]+`(?:, `[^`]+`)*)\)\. \S")
RECOMMENDED = re.compile(r"^- \*\*Recommended\.\*\* \S")
OLD_FILES = ["architecture.md", "conventions.md", "help-standard.md"]
# A whole file name, not the tail of another one (docs/adr/0006-db-table-conventions.md is not conventions.md).
OLD_NAMES = re.compile(r"(?<![\w-])(?:" + "|".join(map(re.escape, OLD_FILES)) + ")")
# Records of the past, like git history: the released changelog and Antagor's task and epic files.
HISTORY = ("docs/adr/", "template/", ".agents/", "CHANGELOG.md", "tests/test_standard_doc.py")


def prose_lines() -> list[str]:
    """The lines of the Standard outside fenced code blocks."""
    lines, fenced = [], False
    for line in STANDARD.read_text().splitlines():
        if line.startswith("```"):
            fenced = not fenced
        elif not fenced:
            lines.append(line)
    return lines


def rules() -> list[str]:
    """Every top-level list item of the Standard: each one is a rule."""
    return [line for line in prose_lines() if line.startswith("- ")]


def test_sections_are_the_named_ones_in_order():
    headings = [line[3:] for line in prose_lines() if line.startswith("## ")]
    parts = [line[4:] for line in prose_lines() if line.startswith("### ")]
    assert headings == SECTIONS
    assert parts == OPTIONAL_PARTS


def test_every_rule_is_marked_and_mandatory_ones_name_a_gate_step():
    found = rules()
    assert len(found) > 40
    unmarked = [rule for rule in found if not (MANDATORY.match(rule) or RECOMMENDED.match(rule))]
    assert unmarked == []
    named = {
        step.strip("`")
        for rule in found
        if (match := MANDATORY.match(rule))
        for step in match["steps"].split(", ")
    }
    assert named - GATE_STEPS == set()
    assert {"standard: commands", "standard: json", "standard: errors", "standard: health"} <= named
    assert {"standard: docs", "standard: ci", "secret scan", "install section", "build + install wheel"} <= named


def test_every_optional_part_says_when_and_how_to_turn_it_on():
    text = STANDARD.read_text()
    bodies = re.split(r"^### ", text.split("\n## Optional parts\n", 1)[1], flags=re.M)[1:]
    assert len(bodies) == len(OPTIONAL_PARTS)
    for body in bodies:
        name = body.splitlines()[0]
        assert "\n**When.** " in body, name
        assert "\n**Turn on.** " in body, name
        assert re.search(r"^- \*\*(Mandatory|Recommended)", body, flags=re.M), name


def test_no_section_numbers():
    assert re.findall(r"§\s*\d", STANDARD.read_text()) == []


def test_old_reference_files_are_gone_and_nothing_names_them():
    reference = STANDARD.parent
    assert sorted(path.name for path in reference.iterdir()) == ["existing-package.md", "standard.md"]
    tracked = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    naming = [
        f"{path}: {name}"
        for path in tracked
        if not path.startswith(HISTORY) and (ROOT / path).is_file()
        for name in OLD_NAMES.findall((ROOT / path).read_text(errors="replace"))
    ]
    assert naming == []
