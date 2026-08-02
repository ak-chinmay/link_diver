"""Environment-backed application configuration."""

from __future__ import annotations

from dataclasses import dataclass
from os import environ
from typing import Mapping, Optional


SUPPORTED_SOURCES = {"todoist", "twitter", "twitter_cookie"}


@dataclass(frozen=True)
class Settings:
    """Configuration required to run Link Diver.

    Attributes:
        telegram_bot_token: Token issued by Telegram's BotFather.
        telegram_chat_id: Destination chat or channel identifier.
        content_source: Comma-separated source names retained for backward
            compatibility. Prefer the :attr:`content_sources` property.
        todoist_token: Todoist API bearer token when Todoist is selected.
        todoist_project_id: Project from which tasks are fetched.
        x_access_token: OAuth user-context token when Twitter is selected.
        x_user_id: Optional authenticated X user ID. When omitted, the API's
            ``/users/me`` endpoint is used.
        x_auth_token: Browser ``auth_token`` cookie for the unofficial,
            cookie-authenticated Twitter source.
        x_bookmark_limit: Maximum number of visible bookmarks collected by the
            browser source before random selection.
        batch_size: Maximum number of content items included in one message.
        request_timeout: HTTP request timeout in seconds.
    """

    telegram_bot_token: str
    telegram_chat_id: str
    content_source: str = "todoist"
    todoist_token: Optional[str] = None
    todoist_project_id: Optional[str] = None
    x_access_token: Optional[str] = None
    x_user_id: Optional[str] = None
    x_auth_token: Optional[str] = None
    x_bookmark_limit: int = 100
    batch_size: int = 1
    request_timeout: float = 30.0

    @property
    def content_sources(self) -> tuple[str, ...]:
        """Return configured source names in processing order."""
        return tuple(self.content_source.split(","))

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
            ValueError: If a numeric limit or source list is invalid.
        """
        source = environ if env is None else env

        def required(name: str) -> str:
            value = source.get(name)
            if not value:
                raise RuntimeError(f"Missing required env var: {name}")
            return value

        batch_size = int(source.get("BATCH_SIZE", "1"))
        request_timeout = float(source.get("REQUEST_TIMEOUT", "30"))
        x_bookmark_limit = int(source.get("X_BOOKMARK_LIMIT", "100"))
        if batch_size < 1:
            raise ValueError("BATCH_SIZE must be at least 1")
        if request_timeout <= 0:
            raise ValueError("REQUEST_TIMEOUT must be greater than 0")
        if x_bookmark_limit < 1:
            raise ValueError("X_BOOKMARK_LIMIT must be at least 1")

        configured_sources = source.get(
            "CONTENT_SOURCES",
            source.get("CONTENT_SOURCE", "todoist"),
        )
        content_sources = tuple(
            name.strip().lower()
            for name in configured_sources.split(",")
            if name.strip()
        )
        if not content_sources:
            raise ValueError("CONTENT_SOURCES must contain at least one source")
        unsupported = set(content_sources) - SUPPORTED_SOURCES
        if unsupported:
            choices = ", ".join(sorted(SUPPORTED_SOURCES))
            raise ValueError(f"CONTENT_SOURCES entries must be one of: {choices}")
        if len(set(content_sources)) != len(content_sources):
            raise ValueError("CONTENT_SOURCES cannot contain duplicates")
        content_source = ",".join(content_sources)

        todoist_token = None
        todoist_project_id = None
        x_access_token = None
        x_auth_token = None
        if "todoist" in content_sources:
            todoist_token = required("TODOIST_TOKEN")
            todoist_project_id = required("TODOIST_PROJECT_ID")
        if "twitter" in content_sources:
            x_access_token = required("X_ACCESS_TOKEN")
        if "twitter_cookie" in content_sources:
            x_auth_token = required("X_AUTH_TOKEN")

        return cls(
            telegram_bot_token=required("TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=required("TELEGRAM_CHAT_ID"),
            content_source=content_source,
            todoist_token=todoist_token,
            todoist_project_id=todoist_project_id,
            x_access_token=x_access_token,
            x_user_id=source.get("X_USER_ID") or None,
            x_auth_token=x_auth_token,
            x_bookmark_limit=x_bookmark_limit,
            batch_size=batch_size,
            request_timeout=request_timeout,
        )
