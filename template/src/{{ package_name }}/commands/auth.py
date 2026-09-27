from __future__ import annotations

import typer
from rich.markup import escape

from .. import output, providers
from ..core.errors import CredentialsUnhealthy, InvalidArguments
from ..core.version import DEV_VERSION, installed_version
from ..credentials import health
from ..credentials import manager as credentials

_CLI = __name__.split(".")[0]

app = output.group("Manage credentials.")


@app.command("login")
@output.guard
def login(
    ctx: typer.Context,
    provider: str = typer.Option("default", "--provider", help="Provider/profile name."),
    non_interactive: bool = output.NonInteractiveOption,
    json_output: bool = output.JsonOption,
    quiet: bool = output.QuietOption,
) -> None:
    """Store a credential for a provider.

    Example: {cli} auth login --provider default
    """
    secret = credentials.read_secret_from_env(provider)
    if secret is None:
        if ctx.obj.get("non_interactive") or non_interactive:
            raise InvalidArguments(
                f"No credential found in environment for provider '{provider}' and --non-interactive was set."
            )
        secret = typer.prompt(f"Enter API key for '{provider}'", hide_input=True)
    credentials.store_secret(provider, secret)
    output.emit_success(
        ctx,
        {"provider": provider},
        render_human=lambda d: output.human.echo(f"Stored credential for '{d['provider']}'."),
    )


@app.command("logout")
@output.guard
def logout(
    ctx: typer.Context,
    provider: str = typer.Option("default", "--provider", help="Provider/profile name."),
    json_output: bool = output.JsonOption,
    quiet: bool = output.QuietOption,
) -> None:
    """Remove a stored credential.

    Example: {cli} auth logout --provider default
    """
    credentials.delete_secret(provider)
    output.emit_success(
        ctx,
        {"provider": provider},
        render_human=lambda d: output.human.echo(f"Removed credential for '{d['provider']}'."),
    )


@app.command("status")
@output.guard
def auth_status(
    ctx: typer.Context,
    check: bool = typer.Option(
        False, "--check", help="Also make one cheap read-only call per provider (10 s timeout) to prove each works."
    ),
    provider: str | None = typer.Option(None, "--provider", help="Report only this provider (default: all)."),
    json_output: bool = output.JsonOption,
    quiet: bool = output.QuietOption,
) -> None:
    """Report every provider's credential: where it comes from and whether it works. Never prints values.

    Without --check only presence is reported (status `unchecked` or `missing`).
    Exits 0 when every required provider is ok/unchecked (an optional one may be
    missing), 3 when any required provider has a problem or any credential is
    invalid/expired, 2 on a usage error. The --json shape is a cross-tool contract:
    `tool`, `version`, `checked_at`, `credentials[]` with `provider`, `required`,
    `fields`, `source`, `source_ref`, `status`, `expires_at`, `quota`, `message`.

    Example: {cli} auth status --check --json
    """
    selected = providers.all_providers()
    if provider is not None:
        selected = [cls for cls in selected if cls.name == provider]
        if not selected:
            known = ", ".join(cls.name for cls in providers.all_providers()) or "none"
            raise InvalidArguments(f"Unknown provider '{provider}' (known: {known}).")
    payload = health.report(_CLI, installed_version() or DEV_VERSION, selected, check=check)
    problems = {entry["provider"]: entry["status"] for entry in payload["credentials"] if health.is_problem(entry)}
    output.emit_report(ctx, payload, _render_status, CredentialsUnhealthy(problems) if problems else None)


def _render_status(payload: dict) -> None:
    if not payload["credentials"]:
        output.human.echo("No providers with credentials.")
    for entry in payload["credentials"]:
        mark = {"ok": "[green]✓[/green]", "unchecked": "[dim]·[/dim]"}.get(entry["status"], "[red]✗[/red]")
        optional = "" if entry["required"] else " (optional)"
        detail = f" — {entry['message']}" if entry["message"] else ""
        expires = f", expires {entry['expires_at']}" if entry["expires_at"] else ""
        line = f"{entry['provider']}{optional}: {entry['status']} ({entry['source']}: {entry['source_ref']}){expires}{detail}"
        output.human.echo(f"{mark} {escape(line)}")
