"""Environment-backed application configuration."""

from __future__ import annotations

from dataclasses import dataclass
from os import environ
from typing import Mapping


@dataclass(frozen=True)
class Settings:
    """Configuration required to run Link Diver.

    Attributes:
        todoist_token: Todoist API bearer token.
        todoist_project_id: Project from which tasks are fetched.
        telegram_bot_token: Token issued by Telegram's BotFather.
        telegram_chat_id: Destination chat or channel identifier.
        batch_size: Maximum number of tasks included in one message.
        request_timeout: HTTP request timeout in seconds.
    """

    todoist_token: str
    todoist_project_id: str
    telegram_bot_token: str
    telegram_chat_id: str
    batch_size: int = 1
    request_timeout: float = 30.0

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        """Create settings from environment variables.

        Args:
            env: Environment-like mapping. Defaults to :data:`os.environ`.
                Supplying a mapping is useful in tests and embedded use.

        Returns:
            A validated settings instance.

        Raises:
            RuntimeError: If a required variable is absent or empty.
            ValueError: If ``BATCH_SIZE`` or ``REQUEST_TIMEOUT`` is invalid.
        """
        source = environ if env is None else env

        def required(name: str) -> str:
            value = source.get(name)
            if not value:
                raise RuntimeError(f"Missing required env var: {name}")
            return value

        batch_size = int(source.get("BATCH_SIZE", "1"))
        request_timeout = float(source.get("REQUEST_TIMEOUT", "30"))
        if batch_size < 1:
            raise ValueError("BATCH_SIZE must be at least 1")
        if request_timeout <= 0:
            raise ValueError("REQUEST_TIMEOUT must be greater than 0")

        return cls(
            todoist_token=required("TODOIST_TOKEN"),
            todoist_project_id=required("TODOIST_PROJECT_ID"),
            telegram_bot_token=required("TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=required("TELEGRAM_CHAT_ID"),
            batch_size=batch_size,
            request_timeout=request_timeout,
        )
