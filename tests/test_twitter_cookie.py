"""Tests for cookie-authenticated X browser scraping."""

from contextlib import contextmanager
from unittest.mock import Mock

import pytest

from link_diver.twitter_cookie import BOOKMARKS_URL, TwitterCookieClient


def browser_fixture(page: Mock):
    """Build a minimal Playwright-compatible object graph."""
    context = Mock()
    context.new_page.return_value = page
    browser = Mock()
    browser.new_context.return_value = context
    playwright = Mock()
    playwright.chromium.launch.return_value = browser

    @contextmanager
    def factory():
        yield playwright

    return factory, playwright, browser, context


def test_get_bookmarks_injects_cookie_and_collects_posts() -> None:
    page = Mock()
    page.url = BOOKMARKS_URL
    page.eval_on_selector_all.side_effect = [
        [{"id": "1", "text": "First", "author_username": "alice"}],
        [
            {"id": "1", "text": "First", "author_username": "alice"},
            {"id": "2", "text": "Second", "author_username": "bob"},
        ],
    ]
    factory, playwright, browser, context = browser_fixture(page)
    client = TwitterCookieClient(
        "private-cookie",
        max_bookmarks=2,
        timeout=4,
        playwright_factory=factory,
    )

    result = client.get_bookmarks()

    assert result == [
        {"id": "1", "text": "First", "author_username": "alice"},
        {"id": "2", "text": "Second", "author_username": "bob"},
    ]
    playwright.chromium.launch.assert_called_once_with(headless=True)
    context.add_cookies.assert_called_once_with(
        [
            {
                "name": "auth_token",
                "value": "private-cookie",
                "domain": ".x.com",
                "path": "/",
                "httpOnly": True,
                "secure": True,
                "sameSite": "None",
            }
        ]
    )
    page.goto.assert_called_once_with(
        BOOKMARKS_URL,
        wait_until="domcontentloaded",
        timeout=4000,
    )
    browser.close.assert_called_once_with()


def test_get_bookmarks_rejects_login_redirect() -> None:
    page = Mock()
    page.url = "https://x.com/i/flow/login"
    factory, _, browser, _ = browser_fixture(page)
    client = TwitterCookieClient(
        "expired-cookie",
        playwright_factory=factory,
    )

    with pytest.raises(RuntimeError, match="rejected or expired"):
        client.get_bookmarks()

    browser.close.assert_called_once_with()


def test_get_bookmarks_handles_empty_bookmarks_page() -> None:
    page = Mock()
    page.url = BOOKMARKS_URL
    page.wait_for_selector.side_effect = TimeoutError
    page.locator.return_value.count.return_value = 0
    page.get_by_text.return_value.count.return_value = 1
    factory, _, _, _ = browser_fixture(page)
    client = TwitterCookieClient(
        "private-cookie",
        playwright_factory=factory,
    )

    assert client.get_bookmarks() == []


def test_get_bookmarks_reports_unloadable_page() -> None:
    page = Mock()
    page.url = BOOKMARKS_URL
    page.wait_for_selector.side_effect = TimeoutError
    page.locator.return_value.count.return_value = 0
    page.get_by_text.return_value.count.return_value = 0
    factory, _, _, _ = browser_fixture(page)
    client = TwitterCookieClient(
        "private-cookie",
        playwright_factory=factory,
    )

    with pytest.raises(RuntimeError, match="cookie may be expired"):
        client.get_bookmarks()
