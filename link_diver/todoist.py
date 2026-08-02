"""Todoist API client."""

from __future__ import annotations

from typing import Any

import requests

TODOIST_API_URL = "https://api.todoist.com/api/v1"


class TodoistClient:
    """Small client for the Todoist endpoints used by Link Diver.

    Args:
        token: Todoist API bearer token.
        timeout: Per-request timeout in seconds.
        session: Optional requests-compatible session for connection reuse or
            dependency injection.
        base_url: Todoist API base URL.
    """

    def __init__(
        self,
        token: str,
        timeout: float = 30.0,
        session: requests.Session | None = None,
        base_url: str = TODOIST_API_URL,
    ) -> None:
        self._timeout = timeout
        self._session = session or requests.Session()
        self._base_url = base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {token}"}

    def get_tasks(self, project_id: str) -> list[dict[str, Any]]:
        """Fetch every active task in a project, following cursor pagination.

        Args:
            project_id: Todoist project identifier.

        Returns:
            Tasks in API order across all result pages.

        Raises:
            requests.HTTPError: If Todoist returns an unsuccessful response.
        """
        tasks: list[dict[str, Any]] = []
        cursor: str | None = None

        while True:
            params: dict[str, str | int] = {
                "project_id": project_id,
                "limit": 200,
            }
            if cursor:
                params["cursor"] = cursor

            data = self._get("tasks", params=params)
            tasks.extend(data.get("results", []))
            cursor = data.get("next_cursor")
            if not cursor:
                return tasks

    def get_section_name(self, section_id: str | None) -> str | None:
        """Return a section name, or ``None`` when a task has no section.

        Args:
            section_id: Todoist section identifier.

        Returns:
            Section name when present.

        Raises:
            requests.HTTPError: If Todoist returns an unsuccessful response.
        """
        if not section_id:
            return None
        data = self._get(f"sections/{section_id}")
        return data.get("name")

    def _get(
        self,
        path: str,
        params: dict[str, str | int] | None = None,
    ) -> dict[str, Any]:
        """Issue an authenticated GET request and decode its JSON object."""
        response = self._session.get(
            f"{self._base_url}/{path}",
            headers=self._headers,
            params=params,
            timeout=self._timeout,
        )
        response.raise_for_status()
        return response.json()
