"""Tests for application orchestration."""

from unittest.mock import Mock

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
