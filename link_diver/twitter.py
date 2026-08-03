"""X API client for retrieving Twitter/X bookmarks."""

from __future__ import annotations

from typing import Any, Optional

import requests

X_API_URL = "https://api.x.com/2"


class TwitterClient:
    """Retrieve bookmarks for the authenticated X user.

    The access token must be an OAuth user-context token with
    ``bookmark.read``, ``tweet.read``, and ``users.read`` scopes. App-only
    bearer tokens cannot access private bookmarks.

    Args:
        access_token: OAuth user-context access token.
        user_id: Authenticated user's ID. If omitted, ``/users/me`` resolves it.
        timeout: Per-request timeout in seconds.
        session: Optional requests-compatible session for dependency injection.
        base_url: X API v2 base URL.
    """

    def __init__(
        self,
        access_token: str,
        user_id: Optional[str] = None,
        timeout: float = 30.0,
        session: Optional[requests.Session] = None,
        base_url: str = X_API_URL,
    ) -> None:
        self._user_id = user_id
        self._timeout = timeout
        self._session = session or requests.Session()
        self._base_url = base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {access_token}"}

    def get_bookmarks(self) -> list[dict[str, Any]]:
        """Fetch all bookmarks, following X pagination tokens.

        Author usernames returned through API expansions are copied to each
        bookmark as ``author_username`` for presentation by downstream code.

        Returns:
            Bookmarked posts in API order across all result pages.

        Raises:
            requests.HTTPError: If X returns an unsuccessful response.
            RuntimeError: If the authenticated user response has no user ID.
        """
        user_id = self._user_id or self.get_authenticated_user_id()
        bookmarks: list[dict[str, Any]] = []
        pagination_token: Optional[str] = None

        while True:
            params = {
                "max_results": 100,
                "expansions": "author_id",
                "tweet.fields": "author_id,created_at",
                "user.fields": "username,name",
            }
            if pagination_token:
                params["pagination_token"] = pagination_token

            data = self._get(f"users/{user_id}/bookmarks", params=params)
            authors = {
                user.get("id"): user.get("username")
                for user in data.get("includes", {}).get("users", [])
            }
            for post in data.get("data", []):
                bookmark = dict(post)
                username = authors.get(post.get("author_id"))
                if username:
                    bookmark["author_username"] = username
                bookmarks.append(bookmark)

            pagination_token = data.get("meta", {}).get("next_token")
            if not pagination_token:
                return bookmarks

    def get_authenticated_user_id(self) -> str:
        """Resolve the user ID associated with the access token.

        Returns:
            Authenticated X user ID.

        Raises:
            requests.HTTPError: If X returns an unsuccessful response.
            RuntimeError: If the response does not contain an ID.
        """
        data = self._get("users/me")
        user_id = data.get("data", {}).get("id")
        if not user_id:
            raise RuntimeError("X API did not return an authenticated user ID")
        self._user_id = user_id
        return user_id

    def _get(
        self,
        path: str,
        params: Optional[dict[str, Any]] = None,
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
