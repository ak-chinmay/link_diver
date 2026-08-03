"""Pure selection and Telegram formatting for X bookmarks."""

from __future__ import annotations

import html
import random
from collections.abc import Callable, Sequence
from typing import Any

Bookmark = dict[str, Any]


def format_bookmark(bookmark: Bookmark, index: int, show_index: bool) -> str:
    """Format one X bookmark as Telegram-safe HTML.

    Args:
        bookmark: Post returned by the X bookmarks API.
        index: One-based position in the selected bookmark list.
        show_index: Whether to include the position in the heading.

    Returns:
        Telegram-safe HTML containing author, post text, and a canonical link.
    """
    heading = f"X bookmark {index}" if show_index else "X bookmark"
    lines = [f"<b>{heading}</b>"]

    username = bookmark.get("author_username")
    if username:
        lines.append(f"@{html.escape(str(username))}")

    text = str(bookmark.get("text") or "Post content is unavailable.")
    lines.append(html.escape(text))

    post_id = bookmark.get("id")
    if post_id:
        author_path = str(username) if username else "i/web"
        url = f"https://x.com/{author_path}/status/{post_id}"
        lines.append(f'<a href="{html.escape(url, quote=True)}">View post on X</a>')

    return "\n".join(lines)


def build_bookmarks_message(
    bookmarks: Sequence[Bookmark],
    batch_size: int,
    sampler: Callable[[Sequence[Bookmark], int], list[Bookmark]] = random.sample,
) -> str:
    """Randomly select bookmarks and build a Telegram message.

    Args:
        bookmarks: Available X bookmarks.
        batch_size: Maximum number of bookmarks to include.
        sampler: Selection function compatible with :func:`random.sample`.

    Returns:
        Complete Telegram HTML message, or a no-bookmarks notice.

    Raises:
        ValueError: If ``batch_size`` is less than one.
    """
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")
    if not bookmarks:
        return "No bookmarks found for this X account."

    selected = sampler(bookmarks, min(batch_size, len(bookmarks)))
    return "\n\n".join(
        format_bookmark(bookmark, index, batch_size > 1)
        for index, bookmark in enumerate(selected, start=1)
    )
