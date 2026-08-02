"""Content source adapters used by the application service."""

from __future__ import annotations

import random
from collections.abc import Callable, Sequence
from typing import Any, Protocol

from link_diver.formatting import build_message, format_task
from link_diver.todoist import TodoistClient
from link_diver.twitter_formatting import build_bookmarks_message, format_bookmark


class ContentSource(Protocol):
    """Interface for a source that can produce one Telegram message."""

    def build_message(self) -> str:
        """Retrieve, select, and format source content."""


class BookmarkClient(Protocol):
    """Interface shared by official API and browser bookmark clients."""

    def get_bookmarks(self) -> list[dict[str, Any]]:
        """Retrieve bookmarks accessible to the authenticated user."""


class CandidateSource(ContentSource, Protocol):
    """Content source that exposes every item for cross-source selection."""

    def get_candidates(self) -> list[str]:
        """Retrieve and format all eligible content items."""


class TodoistSource:
    """Build messages from randomly selected Todoist tasks."""

    def __init__(
        self,
        client: TodoistClient,
        project_id: str,
        batch_size: int = 1,
    ) -> None:
        self._client = client
        self._project_id = project_id
        self._batch_size = batch_size

    def build_message(self) -> str:
        """Retrieve Todoist tasks and format a random selection."""
        return build_message(
            self._client.get_tasks(self._project_id),
            batch_size=self._batch_size,
            section_resolver=self._client.get_section_name,
        )

    def get_candidates(self) -> list[str]:
        """Retrieve and individually format all Todoist tasks."""
        tasks = self._client.get_tasks(self._project_id)
        return [
            format_task(
                task,
                index=index,
                show_index=False,
                section_resolver=self._client.get_section_name,
            )
            for index, task in enumerate(tasks, start=1)
        ]


class TwitterBookmarksSource:
    """Build messages from randomly selected X bookmarks."""

    def __init__(self, client: BookmarkClient, batch_size: int = 1) -> None:
        self._client = client
        self._batch_size = batch_size

    def build_message(self) -> str:
        """Retrieve X bookmarks and format a random selection."""
        return build_bookmarks_message(
            self._client.get_bookmarks(),
            batch_size=self._batch_size,
        )

    def get_candidates(self) -> list[str]:
        """Retrieve and individually format all X bookmarks."""
        return [
            format_bookmark(bookmark, index=index, show_index=False)
            for index, bookmark in enumerate(
                self._client.get_bookmarks(),
                start=1,
            )
        ]


class SequentialSources:
    """Process sources sequentially and choose one item from the combined pool.

    Args:
        sources: Candidate sources in the order they must be processed.
        chooser: Selection function compatible with :func:`random.choice`.
    """

    def __init__(
        self,
        sources: Sequence[CandidateSource],
        chooser: Callable[[Sequence[str]], str] = random.choice,
    ) -> None:
        if not sources:
            raise ValueError("sources must not be empty")
        self._sources = sources
        self._chooser = chooser

    def build_message(self) -> str:
        """Collect every source in order and select one combined candidate."""
        candidates: list[str] = []
        for source in self._sources:
            candidates.extend(source.get_candidates())
        if not candidates:
            return "No content found in the configured sources."
        return self._chooser(candidates)
