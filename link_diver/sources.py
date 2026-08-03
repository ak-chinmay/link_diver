"""Content source adapters used by the application service."""

from __future__ import annotations

from typing import Any, Protocol

from link_diver.formatting import build_message
from link_diver.todoist import TodoistClient
from link_diver.twitter_formatting import build_bookmarks_message


class ContentSource(Protocol):
    """Interface for a source that can produce one Telegram message."""

    def build_message(self) -> str:
        """Retrieve, select, and format source content."""


class BookmarkClient(Protocol):
    """Interface shared by official API and browser bookmark clients."""

    def get_bookmarks(self) -> list[dict[str, Any]]:
        """Retrieve bookmarks accessible to the authenticated user."""


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
