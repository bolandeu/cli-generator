from __future__ import annotations

from typing import Protocol


class Provider(Protocol):
    """Extension point for external integrations (APIs, LLMs, etc.).

    Implement this in a new module under `providers/` for each backend the
    project needs; keep API calls out of `commands/` and `core/services.py`.
    """

    name: str

    def call(self, *args, **kwargs): ...
