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
    ],
)
def test_from_env_rejects_non_positive_values(
    key: str,
    value: str,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        Settings.from_env({**REQUIRED_ENV, key: value})
