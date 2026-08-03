"""Application orchestration for Link Diver."""

from __future__ import annotations

from collections.abc import Sequence

from link_diver.sources import ContentSource
from link_diver.telegram import TelegramClient


class LinkDiverService:
    """Coordinate task retrieval, formatting, and Telegram delivery.

    Args:
        source: One configured source or an ordered sequence of sources.
        telegram: Configured Telegram client.
    """

    def __init__(
        self,
        source: ContentSource | Sequence[ContentSource],
        telegram: TelegramClient,
    ) -> None:
        self._sources = [source] if hasattr(source, "build_message") else list(source)
        if not self._sources:
            raise ValueError("At least one content source is required")
        self._telegram = telegram

    def run(self) -> str:
        """Run one delivery cycle.

        Each source independently selects its message, and messages are sent in
        configured source order.

        Returns:
            Delivered messages joined with a blank line. For a single source,
            this is exactly the delivered message.

        Raises:
            requests.HTTPError: If either remote service rejects a request.
        """
        messages = []
        for source in self._sources:
            message = source.build_message()
            self._telegram.send_message(message)
            messages.append(message)
        return "\n\n".join(messages)
