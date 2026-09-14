from __future__ import annotations


class CliError(Exception):
    """Base error for all expected, user-facing CLI failures.

    Every raise carries a stable `code`, a human `message`, an optional
    `action` telling the caller (human or agent) how to recover, and the
    process exit code to use. Unexpected failures should NOT be wrapped in
    this — let them surface as tracebacks (exit 1) instead of being hidden.
    """

    def __init__(
        self,
        code: str,
        message: str,
        *,
        action: str | None = None,
        exit_code: int = 1,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.action = action
        self.exit_code = exit_code

    def to_dict(self) -> dict:
        payload: dict = {"code": self.code, "message": self.message}
        if self.action:
            payload["action"] = self.action
        return payload


class ProjectNotInitialized(CliError):
    def __init__(self, path: str) -> None:
        super().__init__(
            "PROJECT_NOT_INITIALIZED",
            f"No project found at or above '{path}'.",
            action="Run '<cli> init' in the project directory.",
            exit_code=4,
        )


class AuthRequired(CliError):
    def __init__(self, provider: str) -> None:
        super().__init__(
            "AUTH_REQUIRED",
            f"Authentication is required for provider '{provider}'.",
            action="Run '<cli> auth login'.",
            exit_code=3,
        )


class InvalidArguments(CliError):
    def __init__(self, message: str) -> None:
        super().__init__("INVALID_ARGUMENTS", message, exit_code=2)


class CredentialStoreUnavailable(CliError):
    def __init__(self, provider: str, reason: str) -> None:
        super().__init__(
            "CREDENTIAL_STORE_UNAVAILABLE",
            f"Could not access the OS credential store for provider '{provider}': {reason}",
            action="Set the credential via an environment variable instead of 'auth login' (see 'auth login --help').",
            exit_code=1,
        )
