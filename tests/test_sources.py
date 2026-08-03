"""Tests for content source adapters."""

from unittest.mock import Mock, patch

from link_diver.sources import TodoistSource, TwitterBookmarksSource


def test_todoist_source_builds_message_from_tasks() -> None:
    client = Mock()
    client.get_tasks.return_value = [{"content": "Task"}]
    client.get_section_name.return_value = None

    result = TodoistSource(client, "project-1").build_message()

    assert result == "<b>Task</b>"
    client.get_tasks.assert_called_once_with("project-1")


def test_twitter_source_builds_message_from_bookmarks() -> None:
    client = Mock()
    client.get_bookmarks.return_value = [{"text": "Post"}]

    with patch(
        "link_diver.sources.build_bookmarks_message",
        return_value="formatted post",
    ) as formatter:
        result = TwitterBookmarksSource(client).build_message()

    assert result == "formatted post"
    client.get_bookmarks.assert_called_once_with()
    formatter.assert_called_once_with([{"text": "Post"}], batch_size=1)
