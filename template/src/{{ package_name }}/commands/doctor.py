from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version
from pathlib import Path

import typer

from .. import output
from ..core import services

_PACKAGE_NAME = __name__.split(".")[0]


@output.guard
def doctor(
    ctx: typer.Context,
    json_output: bool = output.JsonOption,
    quiet: bool = output.QuietOption,
    verbose: bool = output.VerboseOption,
) -> None:
    """Run diagnostic checks and report readiness."""
    checks: list[dict] = [{"name": "python", "ok": True}]

    try:
        cli_version = pkg_version(_PACKAGE_NAME)
    except PackageNotFoundError:
        cli_version = "0.0.0-dev"
    checks.append({"name": "cli_version", "ok": True, "detail": cli_version})

    start = Path(ctx.obj.get("project") or Path.cwd())
    output.vecho(ctx, f"Searching for a project root starting at: {start}")
    root = services.find_project_root(start)
    checks.append({"name": "project", "ok": root is not None, "detail": str(root) if root else None})

    if root is not None:
        try:
            services.load_config(root)
            checks.append({"name": "config", "ok": True})
        except Exception as exc:
            checks.append({"name": "config", "ok": False, "detail": str(exc)})

    all_ok = all(check["ok"] for check in checks)
    output.emit_success(
        ctx,
        {"healthy": all_ok, "checks": checks},
        render_human=lambda data: output.human.render_doctor(data["checks"]),
    )
