"""Telegram Bot API client."""

from __future__ import annotations

import requests

TELEGRAM_API_URL = "https://api.telegram.org"


class TelegramClient:
    """Send HTML messages through a Telegram bot.

    Args:
        bot_token: Token issued by Telegram's BotFather.
        chat_id: Destination chat or channel identifier.
        timeout: Per-request timeout in seconds.
        session: Optional requests-compatible session for dependency injection.
        base_url: Telegram API base URL.
    """

    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        timeout: float = 30.0,
        session: requests.Session | None = None,
        base_url: str = TELEGRAM_API_URL,
    ) -> None:
        self._url = f"{base_url.rstrip('/')}/bot{bot_token}/sendMessage"
        self._chat_id = chat_id
        self._timeout = timeout
        self._session = session or requests.Session()

    def send_message(self, message: str) -> None:
        """Send an HTML-formatted message.

        Args:
            message: Telegram-safe HTML message body.

        Raises:
            requests.HTTPError: If Telegram returns an unsuccessful response.
        """
        response = self._session.post(
            self._url,
            json={
                "chat_id": self._chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": False,
            },
            timeout=self._timeout,
        )
        response.raise_for_status()
