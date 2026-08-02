"""Pure task selection and Telegram message formatting."""

from __future__ import annotations

import html
import random
from collections.abc import Callable, Sequence
from typing import Any

Task = dict[str, Any]
SectionResolver = Callable[[str | None], str | None]


def format_task(
    task: Task,
    index: int,
    show_index: bool,
    section_resolver: SectionResolver,
) -> str:
    """Format one Todoist task as Telegram-safe HTML.

    Args:
        task: Todoist task object.
        index: One-based position in the selected task list.
        show_index: Whether to prefix the title with ``index``.
        section_resolver: Function that resolves a section ID to its name.

    Returns:
        A compact HTML representation of the task.
    """
    raw_title = str(task.get("content") or "Untitled task")
    title = html.escape(_normalize_title(raw_title))
    description = html.escape(str(task.get("description") or ""))
    due = task.get("due") or {}
    due_text = due.get("string") or due.get("date")
    labels = task.get("labels") or []
    section = section_resolver(task.get("section_id"))

    heading = f"{index}. {title}" if show_index else title
    lines = [f"<b>{heading}</b>"]
    if due_text:
        lines.append(f"<b>Due</b>: {html.escape(str(due_text))}")
    if labels:
        labels_text = ", ".join(str(label) for label in labels)
        lines.append(f"<b>Labels</b>: {html.escape(labels_text)}")
    if section:
        lines.append(f"<b>Category/Section</b>: {html.escape(section)}")
    if description:
        lines.append(f"Notes: {description}")
    return "\n".join(lines)


def build_message(
    tasks: Sequence[Task],
    batch_size: int,
    section_resolver: SectionResolver,
    sampler: Callable[[Sequence[Task], int], list[Task]] = random.sample,
) -> str:
    """Select tasks and build a Telegram message.

    Args:
        tasks: Available Todoist tasks.
        batch_size: Maximum number of tasks to include.
        section_resolver: Function that resolves section IDs to names.
        sampler: Selection function compatible with :func:`random.sample`.

    Returns:
        The complete Telegram HTML message, or a no-tasks notice.

    Raises:
        ValueError: If ``batch_size`` is less than one.
    """
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")
    if not tasks:
        return "No active tasks found in this Todoist project."

    selected = sampler(tasks, min(batch_size, len(tasks)))
    return "\n\n".join(
        format_task(
            task,
            index=index,
            show_index=batch_size > 1,
            section_resolver=section_resolver,
        )
        for index, task in enumerate(selected, start=1)
    )


def _normalize_title(title: str) -> str:
    """Retain the original link-cleanup behavior without touching HTML."""
    return (
        title.replace("[", "")
        .replace("]", "")
        .replace("(", "\n\n")
        .replace(")", "")
    )
