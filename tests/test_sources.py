"""Tests for content source adapters."""

from unittest.mock import Mock, patch

from link_diver.sources import (
    SequentialSources,
    TodoistSource,
    TwitterBookmarksSource,
)


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


def test_todoist_source_exposes_all_formatted_candidates() -> None:
    client = Mock()
    client.get_tasks.return_value = [
        {"content": "First"},
        {"content": "Second"},
    ]
    client.get_section_name.return_value = None

    result = TodoistSource(client, "project-1").get_candidates()

    assert result == ["<b>First</b>", "<b>Second</b>"]


def test_twitter_source_exposes_all_formatted_candidates() -> None:
    client = Mock()
    client.get_bookmarks.return_value = [
        {"text": "First"},
        {"text": "Second"},
    ]

    result = TwitterBookmarksSource(client).get_candidates()

    assert result == [
        "<b>X bookmark</b>\nFirst",
        "<b>X bookmark</b>\nSecond",
    ]


def test_sequential_sources_combines_in_order_then_selects_one() -> None:
    call_order = []
    todoist = Mock()
    todoist.get_candidates.side_effect = lambda: (
        call_order.append("todoist") or ["task-1", "task-2"]
    )
    twitter = Mock()
    twitter.get_candidates.side_effect = lambda: (
        call_order.append("twitter") or ["post-1", "post-2"]
    )
    seen_candidates = []

    def choose_last(candidates):
        seen_candidates.extend(candidates)
        return candidates[-1]

    result = SequentialSources(
        [todoist, twitter],
        chooser=choose_last,
    ).build_message()

    assert call_order == ["todoist", "twitter"]
    assert seen_candidates == ["task-1", "task-2", "post-1", "post-2"]
    assert result == "post-2"


def test_sequential_sources_handles_all_sources_empty() -> None:
    first = Mock()
    first.get_candidates.return_value = []
    second = Mock()
    second.get_candidates.return_value = []

    result = SequentialSources([first, second]).build_message()

    assert result == "No content found in the configured sources."
