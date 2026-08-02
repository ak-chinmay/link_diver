"""Tests for Todoist and Telegram HTTP adapters."""

from unittest.mock import Mock, call

from link_diver.telegram import TelegramClient
from link_diver.todoist import TodoistClient


def response_with(data: dict) -> Mock:
    """Create a successful response mock with JSON data."""
    response = Mock()
    response.json.return_value = data
    return response


def test_todoist_get_tasks_follows_cursor_pagination() -> None:
    session = Mock()
    first_response = response_with(
        {"results": [{"id": "1"}], "next_cursor": "next"}
    )
    second_response = response_with(
        {"results": [{"id": "2"}], "next_cursor": None}
    )
    session.get.side_effect = [first_response, second_response]
    client = TodoistClient("secret", timeout=7, session=session)

    result = client.get_tasks("project-1")

    assert result == [{"id": "1"}, {"id": "2"}]
    assert session.get.call_args_list == [
        call(
            "https://api.todoist.com/api/v1/tasks",
            headers={"Authorization": "Bearer secret"},
            params={"project_id": "project-1", "limit": 200},
            timeout=7,
        ),
        call(
            "https://api.todoist.com/api/v1/tasks",
            headers={"Authorization": "Bearer secret"},
            params={
                "project_id": "project-1",
                "limit": 200,
                "cursor": "next",
            },
            timeout=7,
        ),
    ]
    first_response.raise_for_status.assert_called_once_with()
    second_response.raise_for_status.assert_called_once_with()


def test_todoist_does_not_request_missing_section() -> None:
    session = Mock()
    client = TodoistClient("secret", session=session)

    assert client.get_section_name(None) is None
    session.get.assert_not_called()


def test_todoist_get_section_name() -> None:
    session = Mock()
    session.get.return_value = response_with({"name": "Learning"})
    client = TodoistClient("secret", session=session)

    assert client.get_section_name("section-1") == "Learning"
    session.get.return_value.raise_for_status.assert_called_once_with()


def test_telegram_sends_expected_payload() -> None:
    session = Mock()
    session.post.return_value = response_with({"ok": True})
    client = TelegramClient("bot-token", "chat-1", timeout=8, session=session)

    client.send_message("<b>Hello</b>")

    session.post.assert_called_once_with(
        "https://api.telegram.org/botbot-token/sendMessage",
        json={
            "chat_id": "chat-1",
            "text": "<b>Hello</b>",
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        },
        timeout=8,
    )
    session.post.return_value.raise_for_status.assert_called_once_with()
