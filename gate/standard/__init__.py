"""The Standard's checks: the gate's `standard` step runs them over the package at `root`."""

from __future__ import annotations

from pathlib import Path


def check(root: Path) -> str:
    """The step's detail line; a failed check raises the gate's StepFailed. No check exists yet."""
    return "no Standard checks yet"
