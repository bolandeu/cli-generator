"""template_drift.py through its command line, against a fake Gitea on a local port."""

import json
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "template_drift.py"

REPOS = ["a", "b", "c"]
ANSWERS = {"a": "_commit: v1.20.0\n_src_path: x\n", "b": "_commit: v1.18.2\n_src_path: x\n"}
TAGS = ["v1.19.0", "v1.20.0", "v1.18.2", "not-a-version"]


def make_handler(status_override):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, code, body=""):
            data = body.encode()
            self.send_response(code)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            path, _, query = self.path.partition("?")
            page = dict(p.split("=") for p in query.split("&") if p).get("page", "1")
            if status_override:
                return self.reply(status_override)
            if path == "/api/v1/orgs/bolandeu/repos":
                items = [{"name": n} for n in REPOS] if page == "1" else []
                return self.reply(200, json.dumps(items))
            if path == "/api/v1/repos/bolandeu/cli-generator/tags":
                items = [{"name": n} for n in TAGS] if page == "1" else []
                return self.reply(200, json.dumps(items))
            prefix, _, name = path.removeprefix("/api/v1/repos/bolandeu/").partition("/raw/")
            if name == ".copier-answers.yml" and prefix in ANSWERS:
                return self.reply(200, ANSWERS[prefix])
            self.reply(404)

    return Handler


@pytest.fixture
def gitea():
    def start(status_override=0):
        server = HTTPServer(("127.0.0.1", 0), make_handler(status_override))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)
        return f"http://127.0.0.1:{server.server_port}"

    servers = []
    yield start
    for server in servers:
        server.shutdown()


def run(base_url, *args):
    return subprocess.run(
        ["uv", "run", "-q", str(SCRIPT), "--base-url", base_url, *args],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
    )


def test_json_lists_current_lagging_and_foreign_repos(gitea):
    result = run(gitea(), "--json")

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "latest": "v1.20.0",
        "repos": [
            {"name": "b", "version": "v1.18.2", "status": "lags"},
            {"name": "c", "version": None, "status": "not_from_template"},
            {"name": "a", "version": "v1.20.0", "status": "current"},
        ],
    }


def test_human_output_is_one_line_per_repo_lagging_first(gitea):
    result = run(gitea())

    assert result.returncode == 0, result.stderr
    assert [line.split() for line in result.stdout.splitlines()] == [
        ["b", "v1.18.2", "lags"],
        ["c", "-", "not_from_template"],
        ["a", "v1.20.0", "current"],
    ]


def test_server_error_prints_named_error_with_url_and_no_table(gitea):
    base_url = gitea(status_override=503)

    result = run(base_url)

    assert result.returncode != 0
    assert result.stdout == ""
    assert "GiteaError" in result.stderr
    assert f"{base_url}/api/v1/" in result.stderr


def test_unreachable_gitea_prints_named_error_with_url_and_no_table():
    base_url = "http://127.0.0.1:9"

    result = run(base_url, "--json")

    assert result.returncode != 0
    assert result.stdout == ""
    assert "GiteaError" in result.stderr
    assert base_url in result.stderr
