"""Unofficial browser client for cookie-authenticated X bookmarks."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Optional

BOOKMARKS_URL = "https://x.com/i/bookmarks"
TWEET_SELECTOR = '[data-testid="tweet"]'

# Executed in the browser against all currently rendered post articles. Keeping
# DOM parsing in one expression makes the browser boundary easy to test.
EXTRACT_BOOKMARKS_SCRIPT = r"""
(articles) => articles.map((article) => {
  const textNode = article.querySelector('[data-testid="tweetText"]');
  const statusLink = Array.from(article.querySelectorAll('a[href*="/status/"]'))
    .map((anchor) => anchor.getAttribute('href'))
    .find((href) => /^\/[^/]+\/status\/\d+/.test(href || ''));
  if (!textNode || !statusLink) return null;
  const match = statusLink.match(/^\/([^/]+)\/status\/(\d+)/);
  if (!match) return null;
  return {
    id: match[2],
    text: textNode.innerText,
    author_username: match[1]
  };
}).filter(Boolean)
"""


class TwitterCookieClient:
    """Scrape the authenticated user's bookmarks with a browser session.

    This adapter uses X's website rather than its supported API. Website DOM
    changes, authentication challenges, or anti-automation controls can break
    it without notice.

    Args:
        auth_token: Value of X's browser ``auth_token`` cookie.
        max_bookmarks: Maximum bookmarks to collect before returning.
        timeout: Navigation and selector timeout in seconds.
        playwright_factory: Optional ``sync_playwright``-compatible factory for
            tests. The real Playwright dependency is imported lazily.
    """

    def __init__(
        self,
        auth_token: str,
        max_bookmarks: int = 100,
        timeout: float = 30.0,
        playwright_factory: Optional[Callable[[], Any]] = None,
    ) -> None:
        if max_bookmarks < 1:
            raise ValueError("max_bookmarks must be at least 1")
        self._auth_token = auth_token
        self._max_bookmarks = max_bookmarks
        self._timeout_ms = int(timeout * 1000)
        self._playwright_factory = playwright_factory

    def get_bookmarks(self) -> list[dict[str, Any]]:
        """Collect visible bookmarks from the signed-in X bookmarks page.

        Returns:
            Deduplicated bookmarks up to ``max_bookmarks``.

        Raises:
            RuntimeError: If X redirects to login or no bookmark posts can be
                loaded. An empty bookmarks page returns an empty list.
        """
        factory = self._playwright_factory
        if factory is None:
            from playwright.sync_api import sync_playwright

            factory = sync_playwright

        with factory() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                context = browser.new_context()
                context.add_cookies(
                    [
                        {
                            "name": "auth_token",
                            "value": self._auth_token,
                            "domain": ".x.com",
                            "path": "/",
                            "httpOnly": True,
                            "secure": True,
                            "sameSite": "None",
                        }
                    ]
                )
                page = context.new_page()
                page.goto(
                    BOOKMARKS_URL,
                    wait_until="domcontentloaded",
                    timeout=self._timeout_ms,
                )
                if "/login" in page.url or "/i/flow/login" in page.url:
                    raise RuntimeError("X auth_token was rejected or expired")
                return self._collect_bookmarks(page)
            finally:
                browser.close()

    def _collect_bookmarks(self, page: Any) -> list[dict[str, Any]]:
        """Scroll the timeline and merge currently rendered bookmark cards."""
        try:
            page.wait_for_selector(TWEET_SELECTOR, timeout=self._timeout_ms)
        except Exception as error:
            if page.locator(TWEET_SELECTOR).count() == 0:
                empty_state = page.get_by_text("Save posts for later").count()
                if empty_state:
                    return []
                raise RuntimeError(
                    "Could not load X bookmarks; the cookie may be expired"
                ) from error

        bookmarks: dict[str, dict[str, Any]] = {}
        unchanged_rounds = 0
        previous_count = 0

        while len(bookmarks) < self._max_bookmarks and unchanged_rounds < 3:
            visible = page.eval_on_selector_all(
                TWEET_SELECTOR,
                EXTRACT_BOOKMARKS_SCRIPT,
            )
            for bookmark in visible:
                post_id = bookmark.get("id")
                if post_id:
                    bookmarks[str(post_id)] = bookmark
                if len(bookmarks) >= self._max_bookmarks:
                    break

            if len(bookmarks) == previous_count:
                unchanged_rounds += 1
            else:
                unchanged_rounds = 0
                previous_count = len(bookmarks)

            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(750)

        return list(bookmarks.values())[: self._max_bookmarks]
