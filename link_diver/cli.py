"""Command-line application assembly."""

from __future__ import annotations

from link_diver.config import Settings
from link_diver.service import LinkDiverService
from link_diver.sources import (
    ContentSource,
    TodoistSource,
    TwitterBookmarksSource,
)
from link_diver.telegram import TelegramClient
from link_diver.todoist import TodoistClient
from link_diver.twitter import TwitterClient
from link_diver.twitter_cookie import TwitterCookieClient


def create_service(settings: Settings) -> LinkDiverService:
    """Construct the application service from validated settings.

    Args:
        settings: Runtime application configuration.

    Returns:
        A fully configured Link Diver service.
    """
    telegram = TelegramClient(
        settings.telegram_bot_token,
        settings.telegram_chat_id,
        timeout=settings.request_timeout,
    )
    sources = [
        _create_source(settings, source_name)
        for source_name in settings.content_sources
    ]
    return LinkDiverService(sources, telegram)


def _create_source(settings: Settings, source_name: str) -> ContentSource:
    """Construct one configured source by name."""
    if source_name == "twitter":
        return TwitterBookmarksSource(
            TwitterClient(
                _configured(settings.x_access_token, "X_ACCESS_TOKEN"),
                user_id=settings.x_user_id,
                timeout=settings.request_timeout,
            ),
            settings.batch_size,
        )
    if source_name == "twitter_cookie":
        return TwitterBookmarksSource(
            TwitterCookieClient(
                _configured(settings.x_auth_token, "X_AUTH_TOKEN"),
                max_bookmarks=settings.x_bookmark_limit,
                timeout=settings.request_timeout,
            ),
            settings.batch_size,
        )
    return TodoistSource(
        TodoistClient(
            _configured(settings.todoist_token, "TODOIST_TOKEN"),
            timeout=settings.request_timeout,
        ),
        _configured(settings.todoist_project_id, "TODOIST_PROJECT_ID"),
        settings.batch_size,
    )


def _configured(value: str | None, name: str) -> str:
    """Return a conditionally required setting or raise a clear error."""
    if value is None:
        raise RuntimeError(f"Missing required setting: {name}")
    return value


def main() -> None:
    """Load configuration and run a single delivery cycle."""
    create_service(Settings.from_env()).run()
    print("Sent random content to Telegram.")
