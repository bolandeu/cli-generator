# /// script
# requires-python = ">=3.11"
# dependencies = ["packaging", "pyyaml"]
# ///
"""Report which repos of the Gitea org lag behind the latest template tag.

Reads `_commit` from each repo's `.copier-answers.yml`. Read-only, anonymous.
Usage: uv run scripts/template_drift.py [--json] [--base-url URL]
Settings (base URL, org, template repo, ...) live in template_drift.toml.
"""

import argparse
import json
import re
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

import yaml
from packaging.version import InvalidVersion, Version

SETTINGS_FILE = Path(__file__).with_suffix(".toml")
DESCRIBE_SUFFIX = re.compile(r"-\d+-g[0-9a-f]+$")
STATUS_ORDER = {"lags": 0, "not_from_template": 1, "current": 2}


class GiteaError(Exception):
    pass


def parse_version(text: str) -> Version | None:
    try:
        return Version(DESCRIBE_SUFFIX.sub("", text))
    except InvalidVersion:
        return None


def get(url: str, timeout: int, allow_missing: bool = False) -> bytes | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        if allow_missing and error.code == 404:
            return None
        raise GiteaError(f"GET {url} answered {error.code}") from error
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise GiteaError(f"GET {url} failed: {error}") from error


def get_pages(url: str, settings: dict) -> list[dict]:
    items: list[dict] = []
    page = 1
    while True:
        body = get(f"{url}?page={page}&limit={settings['page_size']}", settings["timeout_seconds"])
        chunk = json.loads(body or b"[]")
        items += chunk
        if len(chunk) < settings["page_size"]:
            return items
        page += 1


def latest_tag(api: str, settings: dict) -> str:
    tags = get_pages(f"{api}/repos/{settings['org']}/{settings['template_repo']}/tags", settings)
    versions = {tag["name"]: parse_version(tag["name"]) for tag in tags}
    valid = {name: version for name, version in versions.items() if version is not None}
    if not valid:
        raise GiteaError(f"no PEP 440 tag in {settings['org']}/{settings['template_repo']}")
    return max(valid, key=valid.__getitem__)


def template_version(api: str, repo: str, settings: dict) -> str | None:
    url = f"{api}/repos/{settings['org']}/{repo}/raw/{settings['answers_file']}"
    body = get(url, settings["timeout_seconds"], allow_missing=True)
    if body is None:
        return None
    try:
        answers = yaml.safe_load(body)
    except yaml.YAMLError as error:
        raise GiteaError(f"GET {url} returned invalid YAML: {error}") from error
    commit = answers.get("_commit") if isinstance(answers, dict) else None
    return commit if isinstance(commit, str) and parse_version(commit) else None


def classify(version: str | None, latest: str) -> str:
    if version is None:
        return "not_from_template"
    return "current" if parse_version(version) >= parse_version(latest) else "lags"


def build_report(settings: dict) -> dict:
    api = f"{settings['base_url'].rstrip('/')}/api/v1"
    latest = latest_tag(api, settings)
    repos = []
    for repo in get_pages(f"{api}/orgs/{settings['org']}/repos", settings):
        version = template_version(api, repo["name"], settings)
        repos.append({"name": repo["name"], "version": version, "status": classify(version, latest)})
    repos.sort(key=lambda repo: (STATUS_ORDER[repo["status"]], repo["name"]))
    return {"latest": latest, "repos": repos}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    parser.add_argument("--base-url", help="Gitea base URL (default: template_drift.toml)")
    args = parser.parse_args()
    settings = tomllib.loads(SETTINGS_FILE.read_text())
    if args.base_url:
        settings["base_url"] = args.base_url
    try:
        report = build_report(settings)
    except GiteaError as error:
        print(f"GiteaError: {error}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for repo in report["repos"]:
            print(repo["name"], repo["version"] or "-", repo["status"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
