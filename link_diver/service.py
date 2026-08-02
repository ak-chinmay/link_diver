"""Application orchestration for Link Diver."""

from __future__ import annotations

from link_diver.formatting import build_message
from link_diver.telegram import TelegramClient
from link_diver.todoist import TodoistClient


class LinkDiverService:
    """Coordinate task retrieval, formatting, and Telegram delivery.

    Args:
        todoist: Configured Todoist client.
        telegram: Configured Telegram client.
        project_id: Project from which tasks are fetched.
        batch_size: Maximum tasks sent in a single message.
    """

    def __init__(
        self,
        todoist: TodoistClient,
        telegram: TelegramClient,
        project_id: str,
        batch_size: int = 1,
    ) -> None:
        self._todoist = todoist
        self._telegram = telegram
        self._project_id = project_id
        self._batch_size = batch_size

    def run(self) -> str:
        """Run one delivery cycle.

        Returns:
            The message delivered to Telegram.

        Raises:
            requests.HTTPError: If either remote service rejects a request.
        """
        tasks = self._todoist.get_tasks(self._project_id)
        message = build_message(
            tasks,
            batch_size=self._batch_size,
            section_resolver=self._todoist.get_section_name,
        )
        self._telegram.send_message(message)
        return message
