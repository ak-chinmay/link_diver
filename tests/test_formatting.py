"""Tests for task selection and message formatting."""

import pytest

from link_diver.formatting import build_message, format_task


def test_format_task_escapes_all_user_controlled_fields() -> None:
    task = {
        "content": "Read <guide>",
        "description": "Use A & B",
        "due": {"string": "Today < 5"},
        "labels": ["work&life"],
        "section_id": "section-1",
    }

    result = format_task(
        task,
        index=1,
        show_index=False,
        section_resolver=lambda _: "R&D",
    )

    assert result == (
        "<b>Read &lt;guide&gt;</b>\n"
        "<b>Due</b>: Today &lt; 5\n"
        "<b>Labels</b>: work&amp;life\n"
        "<b>Category/Section</b>: R&amp;D\n"
        "Notes: Use A &amp; B"
    )


def test_format_task_normalizes_markdown_style_link_title() -> None:
    result = format_task(
        {"content": "[Article](https://example.com)"},
        index=1,
        show_index=False,
        section_resolver=lambda _: None,
    )

    assert result == "<b>Article\n\nhttps://example.com</b>"


def test_build_message_returns_notice_for_empty_task_list() -> None:
    result = build_message([], 1, section_resolver=lambda _: None)

    assert result == "No active tasks found in this Todoist project."


def test_build_message_uses_sampler_and_numbers_batches() -> None:
    tasks = [{"content": "First"}, {"content": "Second"}]

    result = build_message(
        tasks,
        batch_size=2,
        section_resolver=lambda _: None,
        sampler=lambda population, size: list(reversed(population))[:size],
    )

    assert result == "<b>1. Second</b>\n\n<b>2. First</b>"


def test_build_message_rejects_invalid_batch_size() -> None:
    with pytest.raises(ValueError, match="at least 1"):
        build_message([{"content": "Task"}], 0, lambda _: None)
