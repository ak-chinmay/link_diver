# Link Diver

Link Diver selects one or more active tasks from a Todoist project and sends
them to a Telegram chat. It is designed for scheduled runs from cron, CI, or a
small always-on host.

Link Diver supports Python 3.9 and newer.

## Architecture

The codebase follows a ports-and-adapters-style split without introducing a
framework:

| Module | Responsibility |
| --- | --- |
| `link_diver.config` | Validates environment configuration. |
| `link_diver.todoist` | Retrieves paginated tasks and section names. |
| `link_diver.telegram` | Delivers HTML messages through the Bot API. |
| `link_diver.formatting` | Selects and formats tasks with no direct network access. |
| `link_diver.service` | Coordinates one complete delivery cycle. |
| `link_diver.cli` | Builds dependencies and exposes the CLI entry point. |
| `driver.py` | Preserves the original executable interface. |

Dependencies are passed into the service and API clients, so business logic can
be tested without credentials or network access.

## Configuration

Set these required environment variables:

| Variable | Description |
| --- | --- |
| `TODOIST_TOKEN` | Todoist API bearer token. |
| `TODOIST_PROJECT_ID` | ID of the source Todoist project. |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token. |
| `TELEGRAM_CHAT_ID` | Destination chat or channel ID. |

Optional variables:

| Variable | Default | Description |
| --- | ---: | --- |
| `BATCH_SIZE` | `1` | Maximum tasks selected per run. |
| `REQUEST_TIMEOUT` | `30` | HTTP timeout in seconds. |

Configuration is loaded only when the CLI runs. Importing `link_diver` does not
read secrets or perform network calls.

## Run

Install runtime dependencies and execute either entry point:

```bash
python3 -m pip install -r requirements.txt
python3 driver.py
```

The existing shell wrapper remains available:

```bash
./link_diver.sh
```

## Test

Tests cover configuration validation, escaping and formatting, deterministic
selection, Todoist pagination, Telegram payloads, and service orchestration.

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m pytest
```

No live Todoist or Telegram credentials are required to run the unit tests.

## Public API example

The components can also be assembled explicitly for an embedded use case:

```python
from link_diver import LinkDiverService, Settings
from link_diver.telegram import TelegramClient
from link_diver.todoist import TodoistClient

settings = Settings.from_env()
service = LinkDiverService(
    TodoistClient(settings.todoist_token),
    TelegramClient(settings.telegram_bot_token, settings.telegram_chat_id),
    settings.todoist_project_id,
    settings.batch_size,
)
message = service.run()
```

All public classes and functions use Google-style docstrings documenting their
arguments, return values, and raised errors.
