from __future__ import annotations

import typer

from .. import output
from ..core.errors import InvalidArguments
from ..credentials import manager as credentials

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
    provider: str = typer.Option("default", "--provider", help="Provider/profile name."),
    json_output: bool = output.JsonOption,
    quiet: bool = output.QuietOption,
) -> None:
    """Check whether a credential is available for a provider.

    Example: {cli} auth status --json
    """
    authenticated = credentials.get_secret(provider) is not None
    output.emit_success(
        ctx,
        {"provider": provider, "authenticated": authenticated},
        render_human=lambda d: output.human.echo(
            f"{'Authenticated' if d['authenticated'] else 'Not authenticated'} for '{d['provider']}'."
        ),
    )
