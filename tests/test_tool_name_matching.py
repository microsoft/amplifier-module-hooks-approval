"""Tests for tool name matching in approval rules.

Verifies that _needs_approval correctly identifies tools by their
actual registered names (write_file, edit_file), not short names.
"""

import pytest

from amplifier_module_hooks_approval.approval_hook import ApprovalHook


@pytest.fixture
def hook():
    """Create an ApprovalHook with default config."""
    return ApprovalHook(config={})


class TestToolNameMatching:
    """Verify _needs_approval uses correct tool names."""

    def test_write_file_triggers_approval(self, hook):
        """write_file is the actual tool name and MUST trigger approval."""
        assert hook._needs_approval("write_file", {}) is True

    def test_edit_file_triggers_approval(self, hook):
        """edit_file is the actual tool name and MUST trigger approval."""
        assert hook._needs_approval("edit_file", {}) is True

    def test_bash_still_triggers_approval(self, hook):
        """bash was already correct and must continue to trigger."""
        assert hook._needs_approval("bash", {}) is True

    def test_old_short_name_write_does_not_trigger(self, hook):
        """The short name 'write' does not correspond to any real tool.
        It should NOT trigger approval. This test documents the bug."""
        assert hook._needs_approval("write", {}) is False

    def test_old_short_name_edit_does_not_trigger(self, hook):
        """The short name 'edit' does not correspond to any real tool.
        It should NOT trigger approval. This test documents the bug."""
        assert hook._needs_approval("edit", {}) is False

    def test_read_file_does_not_trigger_approval(self, hook):
        """read_file is read-only and should NOT trigger approval."""
        assert hook._needs_approval("read_file", {}) is False

    def test_grep_does_not_trigger_approval(self, hook):
        """grep is read-only and should NOT trigger approval."""
        assert hook._needs_approval("grep", {}) is False
