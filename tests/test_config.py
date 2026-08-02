"""Tests for environment-backed configuration."""

import pytest

from link_diver.config import Settings


REQUIRED_ENV = {
    "TODOIST_TOKEN": "todoist-token",
    "TODOIST_PROJECT_ID": "project-id",
    "TELEGRAM_BOT_TOKEN": "telegram-token",
    "TELEGRAM_CHAT_ID": "chat-id",
}


def test_from_env_loads_required_values_and_defaults() -> None:
    settings = Settings.from_env(REQUIRED_ENV)

    assert settings.todoist_project_id == "project-id"
    assert settings.batch_size == 1
    assert settings.request_timeout == 30.0
    assert settings.content_source == "todoist"
    assert settings.x_access_token is None


def test_from_env_loads_twitter_without_todoist_credentials() -> None:
    settings = Settings.from_env(
        {
            "CONTENT_SOURCE": "TWITTER",
            "X_ACCESS_TOKEN": "user-access-token",
            "X_USER_ID": "user-1",
            "TELEGRAM_BOT_TOKEN": "telegram-token",
            "TELEGRAM_CHAT_ID": "chat-id",
        }
    )

    assert settings.content_source == "twitter"
    assert settings.x_access_token == "user-access-token"
    assert settings.x_user_id == "user-1"
    assert settings.todoist_token is None


def test_from_env_requires_twitter_access_token_for_twitter_source() -> None:
    env = {
        "CONTENT_SOURCE": "twitter",
        "TELEGRAM_BOT_TOKEN": "telegram-token",
        "TELEGRAM_CHAT_ID": "chat-id",
    }

    with pytest.raises(RuntimeError, match="X_ACCESS_TOKEN"):
        Settings.from_env(env)


def test_from_env_loads_cookie_source_without_api_credentials() -> None:
    settings = Settings.from_env(
        {
            "CONTENT_SOURCE": "twitter_cookie",
            "X_AUTH_TOKEN": "private-cookie",
            "X_BOOKMARK_LIMIT": "25",
            "TELEGRAM_BOT_TOKEN": "telegram-token",
            "TELEGRAM_CHAT_ID": "chat-id",
        }
    )

    assert settings.content_source == "twitter_cookie"
    assert settings.x_auth_token == "private-cookie"
    assert settings.x_bookmark_limit == 25
    assert settings.x_access_token is None


def test_from_env_loads_multiple_sources_in_declared_order() -> None:
    settings = Settings.from_env(
        {
            **REQUIRED_ENV,
            "CONTENT_SOURCES": " todoist, twitter_cookie ",
            "X_AUTH_TOKEN": "private-cookie",
        }
    )

    assert settings.content_sources == ("todoist", "twitter_cookie")
    assert settings.todoist_token == "todoist-token"
    assert settings.x_auth_token == "private-cookie"


def test_from_env_rejects_duplicate_sources() -> None:
    with pytest.raises(ValueError, match="duplicates"):
        Settings.from_env(
            {**REQUIRED_ENV, "CONTENT_SOURCES": "todoist,todoist"}
        )


def test_from_env_requires_auth_token_for_cookie_source() -> None:
    env = {
        "CONTENT_SOURCE": "twitter_cookie",
        "TELEGRAM_BOT_TOKEN": "telegram-token",
        "TELEGRAM_CHAT_ID": "chat-id",
    }

    with pytest.raises(RuntimeError, match="X_AUTH_TOKEN"):
        Settings.from_env(env)


def test_from_env_rejects_unknown_source() -> None:
    with pytest.raises(ValueError, match="CONTENT_SOURCE"):
        Settings.from_env({**REQUIRED_ENV, "CONTENT_SOURCE": "rss"})


def test_from_env_loads_optional_numeric_values() -> None:
    settings = Settings.from_env(
        {**REQUIRED_ENV, "BATCH_SIZE": "3", "REQUEST_TIMEOUT": "4.5"}
    )

    assert settings.batch_size == 3
    assert settings.request_timeout == 4.5


def test_from_env_reports_missing_variable() -> None:
    env = {**REQUIRED_ENV, "TODOIST_TOKEN": ""}

    with pytest.raises(RuntimeError, match="TODOIST_TOKEN"):
        Settings.from_env(env)


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("BATCH_SIZE", "0", "at least 1"),
        ("REQUEST_TIMEOUT", "0", "greater than 0"),
        ("X_BOOKMARK_LIMIT", "0", "at least 1"),
    ],
)
def test_from_env_rejects_non_positive_values(
    key: str,
    value: str,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        Settings.from_env({**REQUIRED_ENV, key: value})
