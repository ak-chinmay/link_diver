"""Application orchestration for Link Diver."""

from __future__ import annotations

from link_diver.sources import ContentSource
from link_diver.telegram import TelegramClient


class LinkDiverService:
    """Coordinate task retrieval, formatting, and Telegram delivery.

    Args:
        source: Configured content source.
        telegram: Configured Telegram client.
    """

    def __init__(
        self,
        source: ContentSource,
        telegram: TelegramClient,
    ) -> None:
        self._source = source
        self._telegram = telegram

    def run(self) -> str:
        """Run one delivery cycle.

        Returns:
            The message delivered to Telegram.

        Raises:
            requests.HTTPError: If either remote service rejects a request.
        """
        message = self._source.build_message()
        self._telegram.send_message(message)
        return message
