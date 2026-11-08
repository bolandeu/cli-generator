---
id: CG-IDEA-005
title: 'MCP example in the Standard: log_file needs a real file, not StringIO'
created: '2026-11-08T09:58:26+00:00'
source_project: mcp
source_path: /Users/bolandau/Work/tools/mcp
status: new
benefit: 'Anyone copying an MCP server snippet from the Standard gets a spawn failure
  at the first call: fastmcp passes StdioTransport(log_file=...) straight to subprocess
  as stderr, and io.StringIO has no fileno.'
---

Finding from rb-mcp MCP-001 (2026-11-08):

fastmcp 3.x/4.x StdioTransport(log_file=<TextIO>) forwards the object to anyio/subprocess.Popen as stderr. subprocess needs a real file descriptor, so io.StringIO() raises at spawn time — inside a test it looks like 'the server does not start'.

rb-mcp hit it in its red-phase fixture (tests/mcp/helpers.py) and fixed it by passing a real temporary file, same helper API.

Ask: if the Standard's MCP chapter shows a fixture or a transport with log_file, make it a real opened file (or omit log_file), and mention why StringIO does not work. No change needed in rb-mcp beyond this.
