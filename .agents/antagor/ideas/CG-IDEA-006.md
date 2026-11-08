---
id: CG-IDEA-006
title: The Standard's MCP example must use a real file for transport logs, not StringIO
created: '2026-11-08T09:58:46+00:00'
source_project: cli-generator
source_path: /Users/bolandau/Work/tools/cli-generator
status: new
---

From mcp MCP-001 (8.11): fastmcp 3.x/4.x StdioTransport(log_file=<TextIO>) forwards the object to anyio/subprocess.Popen as stderr, and subprocess needs a real file descriptor, so io.StringIO() fails at spawn — the frozen test helper could not pass unchanged. Check the Standard's MCP snippet (and any starter that copies it): log_file must be a real temporary file, not StringIO. Fix used in the task: a real temp file, same helper API.
