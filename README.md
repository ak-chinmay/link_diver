# Link Diver

Link Diver randomly selects content from Todoist tasks or Twitter/X bookmarks
and sends it to a Telegram chat. It is designed for scheduled runs from cron,
CI, or a small always-on host.

Link Diver supports Python 3.9 and newer.

## Architecture

The codebase follows a ports-and-adapters-style split without introducing a
framework:

| Module | Responsibility |
| --- | --- |
| `link_diver.config` | Validates environment configuration. |
| `link_diver.todoist` | Retrieves paginated tasks and section names. |
| `link_diver.twitter` | Retrieves paginated X bookmarks and author details. |
| `link_diver.twitter_cookie` | Reads X bookmarks through an authenticated browser. |
| `link_diver.telegram` | Delivers HTML messages through the Bot API. |
| `link_diver.formatting` | Selects and formats tasks with no direct network access. |
| `link_diver.twitter_formatting` | Selects and formats X bookmarks. |
| `link_diver.sources` | Adapts Todoist and X into a common content interface. |
| `link_diver.service` | Coordinates one complete delivery cycle. |
| `link_diver.cli` | Builds dependencies and exposes the CLI entry point. |
| `driver.py` | Preserves the original executable interface. |

Dependencies are passed into the service and API clients, so business logic can
be tested without credentials or network access.

## Configuration

These Telegram variables are always required:

| Variable | Description |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token. |
| `TELEGRAM_CHAT_ID` | Destination chat or channel ID. |

Optional variables:

| Variable | Default | Description |
| --- | ---: | --- |
| `CONTENT_SOURCES` | `todoist` | Ordered comma-separated providers. |
| `CONTENT_SOURCE` | — | Backward-compatible single-source alternative. |
| `BATCH_SIZE` | `1` | Random items selected from each source. |
| `REQUEST_TIMEOUT` | `30` | HTTP timeout in seconds. |

Supported source names are `todoist`, `twitter` (paid official API), and
`twitter_cookie` (unofficial browser access).

When multiple sources are configured, Link Diver processes each source
sequentially in the listed order. Each source independently selects one random
item and sends its own Telegram message. With
`CONTENT_SOURCES=todoist,twitter_cookie`, every successful run therefore sends
one Todoist message followed by one Twitter bookmark message.

For Todoist plus the free cookie-based Twitter source:

```bash
export CONTENT_SOURCES="todoist,twitter_cookie"
export TODOIST_TOKEN="your-todoist-token"
export TODOIST_PROJECT_ID="your-project-id"
export X_AUTH_TOKEN="your-auth-token-cookie-value"
export X_BOOKMARK_LIMIT="100"
export TELEGRAM_BOT_TOKEN="your-telegram-bot-token"
export TELEGRAM_CHAT_ID="your-chat-id"
export REQUEST_TIMEOUT="30"
python3 driver.py
```

### Todoist source

When `CONTENT_SOURCES` includes `todoist`, set:

| Variable | Description |
| --- | --- |
| `TODOIST_TOKEN` | Todoist API bearer token. |
| `TODOIST_PROJECT_ID` | ID of the source Todoist project. |

### Twitter/X bookmarks source

When `CONTENT_SOURCES` includes `twitter`, set:

| Variable | Required | Description |
| --- | --- | --- |
| `X_ACCESS_TOKEN` | Yes | OAuth user-context access token. |
| `X_USER_ID` | No | Authenticated X user ID; resolved through `/2/users/me` when omitted. |

The X token must be a user-context token with `bookmark.read`, `tweet.read`,
and `users.read` scopes. An app-only bearer token cannot read private bookmarks.
See the official [X bookmarks lookup guide](https://docs.x.com/x-api/posts/bookmarks/quickstart/bookmarks-lookup)
for developer-account and OAuth setup.

Example:

```bash
export CONTENT_SOURCES=twitter
export X_ACCESS_TOKEN="your-oauth-user-access-token"
export TELEGRAM_BOT_TOKEN="your-telegram-bot-token"
export TELEGRAM_CHAT_ID="your-chat-id"
python3 driver.py
```

OAuth access tokens can expire. The scheduled environment must supply a valid
user access token; token issuance and refresh remain the responsibility of the
deployment's secret-management workflow.

### Unofficial cookie source

Include `twitter_cookie` in `CONTENT_SOURCES` to read bookmarks through the X
website without the paid API. Set:

| Variable | Default | Description |
| --- | ---: | --- |
| `X_AUTH_TOKEN` | Required | Value of the `auth_token` cookie from your signed-in X session. |
| `X_BOOKMARK_LIMIT` | `100` | Maximum visible bookmarks collected before selection. |

Install the Chromium runtime once after installing Python dependencies:

```bash
python3 -m playwright install chromium
```

Then run:

```bash
export CONTENT_SOURCES=twitter_cookie
export X_AUTH_TOKEN="your-auth-token-cookie-value"
export TELEGRAM_BOT_TOKEN="your-telegram-bot-token"
export TELEGRAM_CHAT_ID="your-chat-id"
python3 driver.py
```

Treat `X_AUTH_TOKEN` like a password: store it only in an environment variable
or secret manager, never commit or paste it into logs, and rotate it if exposed.
The repository ignores `.env` files to reduce accidental disclosure.

This is an unofficial browser integration. X can change its page structure,
reject automated sessions, expire the cookie, or restrict the account. Review
X's terms for your use case. The client reports login redirects and unloadable
bookmark pages instead of silently sending incorrect content.

For GitHub Actions, set the repository variable `CONTENT_SOURCES` to a value
such as `todoist,twitter_cookie`, then create the Actions secret `X_AUTH_TOKEN`.
Keep the existing Todoist and Telegram secrets. The workflow installs Chromium
only when the cookie source is included.

The included workflow defaults to `todoist,twitter_cookie`. Configure these at
**Repository Settings → Secrets and variables → Actions**:

| Type | Name | Required value |
| --- | --- | --- |
| Secret | `TELEGRAM_BOT_TOKEN` | Telegram bot token. |
| Secret | `TELEGRAM_CHAT_ID` | Destination chat ID. |
| Secret | `TODOIST_TOKEN` | Todoist API token. |
| Secret | `TODOIST_PROJECT_ID` | Todoist project ID. |
| Secret | `X_AUTH_TOKEN` | X browser `auth_token` cookie value. |
| Variable | `CONTENT_SOURCES` | Optional; defaults to `todoist,twitter_cookie`. |
| Variable | `X_BOOKMARK_LIMIT` | Optional; defaults to `100`. |
| Variable | `REQUEST_TIMEOUT` | Optional; defaults to `30` seconds. |

`X_ACCESS_TOKEN` and `X_USER_ID` are needed only when the paid `twitter` source
is included. The workflow validates configuration before attempting delivery,
and scheduled runs do not overlap.

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

Tests cover conditional configuration, escaping and formatting, deterministic
selection, Todoist and X pagination, author expansion, Telegram payloads,
source adapters, and service orchestration.

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m pytest
```

No live Todoist, X, or Telegram credentials are required to run the unit tests.

## Public API example

The components can also be assembled explicitly for an embedded use case:

```python
from link_diver import LinkDiverService, Settings
from link_diver.sources import TwitterBookmarksSource
from link_diver.telegram import TelegramClient
from link_diver.twitter import TwitterClient

settings = Settings.from_env()
service = LinkDiverService(
    TwitterBookmarksSource(
        TwitterClient(settings.x_access_token, user_id=settings.x_user_id)
    ),
    TelegramClient(settings.telegram_bot_token, settings.telegram_chat_id),
)
message = service.run()
```

All public classes and functions use Google-style docstrings documenting their
arguments, return values, and raised errors.
