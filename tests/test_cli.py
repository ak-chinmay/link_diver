"""Tests for source-specific application assembly."""

from unittest.mock import Mock, call, patch

from link_diver.cli import create_service
from link_diver.config import Settings


def test_create_service_assembles_twitter_source() -> None:
    settings = Settings(
        telegram_bot_token="telegram-token",
        telegram_chat_id="chat-1",
        content_source="twitter",
        x_access_token="x-token",
        x_user_id="user-1",
        batch_size=1,
        request_timeout=6,
    )
    twitter_client = Mock()
    twitter_source = Mock()
    telegram_client = Mock()

    with patch(
        "link_diver.cli.TwitterClient",
        return_value=twitter_client,
    ) as client:
        with patch(
            "link_diver.cli.TwitterBookmarksSource",
            return_value=twitter_source,
        ) as source:
            with patch(
                "link_diver.cli.TelegramClient",
                return_value=telegram_client,
            ) as telegram:
                service = create_service(settings)

    client.assert_called_once_with(
        "x-token",
        user_id="user-1",
        timeout=6,
    )
    source.assert_called_once_with(twitter_client, 1)
    telegram.assert_called_once_with(
        "telegram-token",
        "chat-1",
        timeout=6,
    )

    twitter_source.build_message.return_value = "post"
    assert service.run() == "post"
    telegram_client.send_message.assert_called_once_with("post")


def test_create_service_assembles_cookie_browser_source() -> None:
    settings = Settings(
        telegram_bot_token="telegram-token",
        telegram_chat_id="chat-1",
        content_source="twitter_cookie",
        x_auth_token="private-cookie",
        x_bookmark_limit=20,
        request_timeout=7,
    )
    cookie_client = Mock()
    twitter_source = Mock()
    telegram_client = Mock()

    with patch(
        "link_diver.cli.TwitterCookieClient",
        return_value=cookie_client,
    ) as client:
        with patch(
            "link_diver.cli.TwitterBookmarksSource",
            return_value=twitter_source,
        ) as source:
            with patch(
                "link_diver.cli.TelegramClient",
                return_value=telegram_client,
            ):
                service = create_service(settings)

    client.assert_called_once_with(
        "private-cookie",
        max_bookmarks=20,
        timeout=7,
    )
    source.assert_called_once_with(cookie_client, 1)
    twitter_source.build_message.return_value = "cookie post"
    assert service.run() == "cookie post"
    telegram_client.send_message.assert_called_once_with("cookie post")


def test_create_service_assembles_sources_in_configured_order() -> None:
    settings = Settings(
        telegram_bot_token="telegram-token",
        telegram_chat_id="chat-1",
        content_source="todoist,twitter_cookie",
        todoist_token="todoist-token",
        todoist_project_id="project-1",
        x_auth_token="private-cookie",
    )
    todoist_source = Mock()
    twitter_source = Mock()
    combined_source = Mock()
    telegram_client = Mock()

    with patch(
        "link_diver.cli._create_source",
        side_effect=[todoist_source, twitter_source],
    ) as source_factory:
        with patch(
            "link_diver.cli.SequentialSources",
            return_value=combined_source,
        ) as aggregator:
            with patch(
                "link_diver.cli.TelegramClient",
                return_value=telegram_client,
            ):
                service = create_service(settings)

    assert source_factory.call_args_list == [
        call(settings, "todoist"),
        call(settings, "twitter_cookie"),
    ]
    aggregator.assert_called_once_with([todoist_source, twitter_source])
    combined_source.build_message.return_value = "selected item"
    assert service.run() == "selected item"
    telegram_client.send_message.assert_called_once_with("selected item")
