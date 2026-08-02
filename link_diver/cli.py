"""Command-line application assembly."""

from link_diver.config import Settings
from link_diver.service import LinkDiverService
from link_diver.telegram import TelegramClient
from link_diver.todoist import TodoistClient


def create_service(settings: Settings) -> LinkDiverService:
    """Construct the application service from validated settings.

    Args:
        settings: Runtime application configuration.

    Returns:
        A fully configured Link Diver service.
    """
    todoist = TodoistClient(
        settings.todoist_token,
        timeout=settings.request_timeout,
    )
    telegram = TelegramClient(
        settings.telegram_bot_token,
        settings.telegram_chat_id,
        timeout=settings.request_timeout,
    )
    return LinkDiverService(
        todoist,
        telegram,
        settings.todoist_project_id,
        settings.batch_size,
    )


def main() -> None:
    """Load configuration and run a single delivery cycle."""
    create_service(Settings.from_env()).run()
    print("Sent random Todoist tasks to Telegram.")
