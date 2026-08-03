"""Tests for application orchestration."""

from unittest.mock import Mock, call

from link_diver.service import LinkDiverService


def test_run_builds_and_sends_source_message() -> None:
    source = Mock()
    source.build_message.return_value = "<b>Test content</b>"
    telegram = Mock()
    service = LinkDiverService(source, telegram)

    message = service.run()

    assert message == "<b>Test content</b>"
    source.build_message.assert_called_once_with()
    telegram.send_message.assert_called_once_with("<b>Test content</b>")


def test_run_sends_one_message_per_source_in_order() -> None:
    first = Mock()
    first.build_message.return_value = "todoist message"
    second = Mock()
    second.build_message.return_value = "twitter message"
    telegram = Mock()
    service = LinkDiverService([first, second], telegram)

    result = service.run()

    assert result == "todoist message\n\ntwitter message"
    assert telegram.send_message.call_args_list == [
        call("todoist message"),
        call("twitter message"),
    ]
