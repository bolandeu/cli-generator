from __future__ import annotations

import functools
from collections.abc import Callable

import typer

from ..core.errors import CliError, InvalidArguments
from . import human
from . import json as json_output

__all__ = [
    "human",
    "emit_success",
    "emit_error",
    "guard",
    "is_dry_run",
    "require_confirmation",
    "vecho",
    "JsonOption",
    "QuietOption",
    "DryRunOption",
    "ConfirmOption",
    "VerboseOption",
    "NonInteractiveOption",
]

# Reusable local options: attach to any command so `<cli> <command> --json`
# works, on top of the global `<cli> --json <command>` handled by guard().
JsonOption = typer.Option(False, "--json", help="Emit machine-readable JSON output.")
QuietOption = typer.Option(False, "--quiet", help="Suppress non-essential output.")
DryRunOption = typer.Option(False, "--dry-run", help="Show what would happen without making changes.")
ConfirmOption = typer.Option(
    False, "--confirm", help="Confirm a destructive action (required together with --non-interactive)."
)
VerboseOption = typer.Option(False, "--verbose", help="Emit extra diagnostic output.")
NonInteractiveOption = typer.Option(False, "--non-interactive", help="Never prompt; fail instead.")


def emit_success(ctx: typer.Context, payload: dict, render_human: Callable[[dict], None]) -> None:
    if ctx.obj.get("json"):
        json_output.emit({"ok": True, **payload})
    elif not ctx.obj.get("quiet"):
        render_human(payload)


def emit_error(ctx: typer.Context, error: CliError) -> None:
    if ctx.obj.get("json"):
        json_output.emit({"ok": False, "error": error.to_dict()})
    else:
        human.console.print(f"[red]Error:[/red] {error.message}")
        if error.action:
            human.console.print(f"[dim]{error.action}[/dim]")
    raise typer.Exit(code=error.exit_code)


_LOCAL_FLAG_TO_CTX_KEY = {
    "json_output": "json",
    "quiet": "quiet",
    "verbose": "verbose",
    "non_interactive": "non_interactive",
    "dry_run": "dry_run",
}


def is_dry_run(ctx: typer.Context) -> bool:
    return bool(ctx.obj.get("dry_run"))


def vecho(ctx: typer.Context, message: str) -> None:
    """Print a diagnostic line, only under --verbose and only in human mode."""
    if ctx.obj.get("verbose") and not ctx.obj.get("json") and not ctx.obj.get("quiet"):
        human.console.print(f"[dim]{message}[/dim]")


def require_confirmation(ctx: typer.Context, description: str, confirm: bool) -> None:
    """Gate an irreversible/external-state-changing action behind confirmation.

    Call this immediately before the action itself (never before a
    --dry-run preview — dry-run should short-circuit earlier and skip this
    entirely). `--confirm` skips the prompt for scripts/agents that already
    got human sign-off; `--non-interactive` without `--confirm` fails
    loudly instead of hanging on a prompt an agent can't answer.
    """
    if confirm:
        return
    if ctx.obj.get("non_interactive"):
        raise InvalidArguments(f"{description} requires --confirm when --non-interactive is set.")
    if not typer.confirm(f"{description}. Continue?"):
        human.console.print("[yellow]Aborted.[/yellow]")
        raise typer.Exit(code=1)


def guard(func: Callable) -> Callable:
    """Route any CliError raised by a command through emit_error.

    Also merges any command-local --json/--quiet/--verbose/--non-interactive
    option into ctx.obj, so both `<cli> --json status` (global, before the
    subcommand) and `<cli> status --json` (local, after it) work the same
    way. Keeps commands free of repeated try/except boilerplate.
    """

    @functools.wraps(func)
    def wrapper(ctx: typer.Context, *args, **kwargs):
        for flag_name, obj_key in _LOCAL_FLAG_TO_CTX_KEY.items():
            if kwargs.get(flag_name):
                ctx.obj[obj_key] = True
        try:
            return func(ctx, *args, **kwargs)
        except CliError as exc:
            emit_error(ctx, exc)

    return wrapper
