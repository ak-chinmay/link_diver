"""Tests for application orchestration."""

from unittest.mock import Mock

from link_diver.service import LinkDiverService


def test_run_fetches_builds_and_sends_message() -> None:
    todoist = Mock()
    todoist.get_tasks.return_value = [{"content": "Test task"}]
    todoist.get_section_name.return_value = None
    telegram = Mock()
    service = LinkDiverService(todoist, telegram, "project-1", batch_size=1)

    message = service.run()

    assert message == "<b>Test task</b>"
    todoist.get_tasks.assert_called_once_with("project-1")
    telegram.send_message.assert_called_once_with("<b>Test task</b>")
