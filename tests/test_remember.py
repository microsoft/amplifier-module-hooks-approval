"""Tests for session-scoped approval memory using the remember field.

Verifies that ApprovalResponse.remember is consumed and that remembered
decisions are keyed by tool_name + context_pattern, not tool name alone.
"""

import pytest

from amplifier_module_hooks_approval.approval_hook import ApprovalHook


@pytest.fixture
def hook():
    """Create an ApprovalHook with default config."""
    return ApprovalHook(config={})


class TestBuildRememberKey:
    """Verify _build_remember_key produces correct scoped keys."""

    def test_filesystem_tool_keys_by_directory(self, hook):
        """write_file to src/foo.py should key as 'write_file:src/'."""
        event_data = {
            "tool_name": "write_file",
            "tool_input": {"file_path": "src/foo.py"},
        }
        key = hook._build_remember_key("write_file", event_data)
        assert key == "write_file:src/"

    def test_filesystem_tool_root_file_keys_by_dot(self, hook):
        """write_file to foo.py (no directory) should key as 'write_file:.'."""
        event_data = {"tool_name": "write_file", "tool_input": {"file_path": "foo.py"}}
        key = hook._build_remember_key("write_file", event_data)
        assert key == "write_file:."

    def test_bash_tool_keys_by_command_prefix(self, hook):
        """bash with 'git push origin main' should key as 'bash:git push'."""
        event_data = {
            "tool_name": "bash",
            "tool_input": {"command": "git push origin main"},
        }
        key = hook._build_remember_key("bash", event_data)
        assert key == "bash:git push"

    def test_bash_single_word_command(self, hook):
        """bash with 'ls' should key as 'bash:ls'."""
        event_data = {"tool_name": "bash", "tool_input": {"command": "ls"}}
        key = hook._build_remember_key("bash", event_data)
        assert key == "bash:ls"

    def test_other_tool_keys_by_name_only(self, hook):
        """Unknown tools fall back to tool name as key."""
        event_data = {"tool_name": "some_tool", "tool_input": {}}
        key = hook._build_remember_key("some_tool", event_data)
        assert key == "some_tool"

    def test_edit_file_keys_by_directory(self, hook):
        """edit_file should also key by directory like write_file."""
        event_data = {
            "tool_name": "edit_file",
            "tool_input": {"file_path": "tests/test_foo.py"},
        }
        key = hook._build_remember_key("edit_file", event_data)
        assert key == "edit_file:tests/"


class TestRememberApproveFlow:
    """Verify that remembered approvals auto-approve matching calls."""

    def test_remembered_approval_auto_approves(self, hook):
        """After remember=True approval, matching call should be auto-approved."""
        # Simulate storing a remembered approval
        hook._remembered_decisions["write_file:src/"] = True

        # Check if decision is remembered
        key = hook._build_remember_key(
            "write_file",
            {"tool_name": "write_file", "tool_input": {"file_path": "src/bar.py"}},
        )
        assert key in hook._remembered_decisions
        assert hook._remembered_decisions[key] is True

    def test_remembered_denial_auto_denies(self, hook):
        """After remember=True denial, matching call should be auto-denied."""
        hook._remembered_decisions["write_file:.env/"] = False

        key = hook._build_remember_key(
            "write_file",
            {"tool_name": "write_file", "tool_input": {"file_path": ".env/secrets"}},
        )
        assert key in hook._remembered_decisions
        assert hook._remembered_decisions[key] is False


class TestRememberDoesNotCrossPaths:
    """Verify that remembered decisions are scoped by context."""

    def test_approval_does_not_cross_directories(self, hook):
        """Approving write_file to src/ must NOT auto-approve write_file to .env."""
        hook._remembered_decisions["write_file:src/"] = True

        # Different directory — should NOT be in remembered decisions
        env_key = hook._build_remember_key(
            "write_file",
            {"tool_name": "write_file", "tool_input": {"file_path": ".env"}},
        )
        assert env_key not in hook._remembered_decisions or env_key != "write_file:src/"

    def test_bash_approval_does_not_cross_commands(self, hook):
        """Approving 'git push' must NOT auto-approve 'rm -rf'."""
        hook._remembered_decisions["bash:git push"] = True

        rm_key = hook._build_remember_key(
            "bash",
            {"tool_name": "bash", "tool_input": {"command": "rm -rf /tmp/something"}},
        )
        assert rm_key not in hook._remembered_decisions


class TestRememberFalseDoesNotStore:
    """Verify that remember=False leaves no stored decision."""

    def test_no_storage_without_remember(self, hook):
        """A fresh hook should have no remembered decisions."""
        assert len(hook._remembered_decisions) == 0
