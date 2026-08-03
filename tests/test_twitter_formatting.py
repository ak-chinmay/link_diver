"""Tests for X bookmark message formatting."""

import pytest

from link_diver.twitter_formatting import (
    build_bookmarks_message,
    format_bookmark,
)


def test_format_bookmark_escapes_content_and_adds_canonical_link() -> None:
    result = format_bookmark(
        {
            "id": "123",
            "text": "A <useful> post & thread",
            "author_username": "alice&bob",
        },
        index=1,
        show_index=False,
    )

    assert result == (
        "<b>X bookmark</b>\n"
        "@alice&amp;bob\n"
        "A &lt;useful&gt; post &amp; thread\n"
        '<a href="https://x.com/alice&amp;bob/status/123">View post on X</a>'
    )


def test_format_bookmark_uses_fallback_link_without_author() -> None:
    result = format_bookmark(
        {"id": "123", "text": "Post"},
        index=1,
        show_index=False,
    )

    assert 'href="https://x.com/i/web/status/123"' in result


def test_build_bookmarks_message_selects_random_bookmark() -> None:
    bookmarks = [{"text": "First"}, {"text": "Second"}]

    result = build_bookmarks_message(
        bookmarks,
        batch_size=1,
        sampler=lambda population, size: [population[1]],
    )

    assert result == "<b>X bookmark</b>\nSecond"


def test_build_bookmarks_message_handles_empty_results() -> None:
    assert (
        build_bookmarks_message([], batch_size=1)
        == "No bookmarks found for this X account."
    )


def test_build_bookmarks_message_rejects_invalid_batch_size() -> None:
    with pytest.raises(ValueError, match="at least 1"):
        build_bookmarks_message([{"text": "Post"}], batch_size=0)
