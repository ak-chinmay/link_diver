"""Tests for the X bookmarks API client."""

from unittest.mock import Mock, call

import pytest

from link_diver.twitter import TwitterClient


def response_with(data: dict) -> Mock:
    """Create a successful response mock with JSON data."""
    response = Mock()
    response.json.return_value = data
    return response


def test_get_bookmarks_paginates_and_attaches_author_username() -> None:
    session = Mock()
    first_response = response_with(
        {
            "data": [{"id": "post-1", "author_id": "author-1", "text": "One"}],
            "includes": {"users": [{"id": "author-1", "username": "alice"}]},
            "meta": {"next_token": "next-page"},
        }
    )
    second_response = response_with(
        {
            "data": [{"id": "post-2", "author_id": "author-2", "text": "Two"}],
            "includes": {"users": [{"id": "author-2", "username": "bob"}]},
            "meta": {"result_count": 1},
        }
    )
    session.get.side_effect = [first_response, second_response]
    client = TwitterClient(
        "access-token",
        user_id="user-1",
        timeout=5,
        session=session,
    )

    result = client.get_bookmarks()

    assert result == [
        {
            "id": "post-1",
            "author_id": "author-1",
            "text": "One",
            "author_username": "alice",
        },
        {
            "id": "post-2",
            "author_id": "author-2",
            "text": "Two",
            "author_username": "bob",
        },
    ]
    common_params = {
        "max_results": 100,
        "expansions": "author_id",
        "tweet.fields": "author_id,created_at",
        "user.fields": "username,name",
    }
    assert session.get.call_args_list == [
        call(
            "https://api.x.com/2/users/user-1/bookmarks",
            headers={"Authorization": "Bearer access-token"},
            params=common_params,
            timeout=5,
        ),
        call(
            "https://api.x.com/2/users/user-1/bookmarks",
            headers={"Authorization": "Bearer access-token"},
            params={**common_params, "pagination_token": "next-page"},
            timeout=5,
        ),
    ]
    first_response.raise_for_status.assert_called_once_with()
    second_response.raise_for_status.assert_called_once_with()


def test_get_bookmarks_resolves_authenticated_user_when_id_is_omitted() -> None:
    session = Mock()
    session.get.side_effect = [
        response_with({"data": {"id": "resolved-user"}}),
        response_with({"data": [], "meta": {"result_count": 0}}),
    ]
    client = TwitterClient("access-token", session=session)

    assert client.get_bookmarks() == []
    assert session.get.call_args_list[0] == call(
        "https://api.x.com/2/users/me",
        headers={"Authorization": "Bearer access-token"},
        params=None,
        timeout=30.0,
    )
    assert "users/resolved-user/bookmarks" in session.get.call_args_list[1].args[0]


def test_get_authenticated_user_id_requires_id_in_response() -> None:
    session = Mock()
    session.get.return_value = response_with({"data": {}})
    client = TwitterClient("access-token", session=session)

    with pytest.raises(RuntimeError, match="authenticated user ID"):
        client.get_authenticated_user_id()
