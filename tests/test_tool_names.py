"""Tests for PR5: correct tool names in high-risk list.

Verifies that write_file / edit_file trigger approval and that the old
names (write, edit) no longer do.
"""
import pytest

from amplifier_module_hooks_approval.approval_hook import ApprovalHook

# Minimal config that disables audit (no filesystem writes during tests)
_CFG = {"audit": {"enabled": False}}


@pytest.fixture
def hook():
    return ApprovalHook(config=_CFG)


# ---------------------------------------------------------------------------
# New correct names MUST trigger approval
# ---------------------------------------------------------------------------


def test_write_file_triggers_approval(hook):
    """write_file is in the high-risk list and must require approval."""
    assert hook._needs_approval("write_file", {}) is True


def test_edit_file_triggers_approval(hook):
    """edit_file is in the high-risk list and must require approval."""
    assert hook._needs_approval("edit_file", {}) is True


def test_bash_triggers_approval(hook):
    """bash always requires approval (handled by its own branch)."""
    assert hook._needs_approval("bash", {"command": "echo hello"}) is True


# ---------------------------------------------------------------------------
# Old stale names must NOT trigger approval (regression guard)
# ---------------------------------------------------------------------------


def test_old_write_does_not_trigger_approval(hook):
    """'write' was removed from high-risk list; should NOT trigger approval."""
    assert hook._needs_approval("write", {}) is False


def test_old_edit_does_not_trigger_approval(hook):
    """'edit' was removed from high-risk list; should NOT trigger approval."""
    assert hook._needs_approval("edit", {}) is False


# ---------------------------------------------------------------------------
# Read-only / search tools must NOT trigger approval
# ---------------------------------------------------------------------------


def test_read_file_does_not_trigger_approval(hook):
    assert hook._needs_approval("read_file", {}) is False


def test_grep_does_not_trigger_approval(hook):
    assert hook._needs_approval("grep", {}) is False


def test_glob_does_not_trigger_approval(hook):
    assert hook._needs_approval("glob", {}) is False


# ---------------------------------------------------------------------------
# Other high-risk tools must still trigger approval
# ---------------------------------------------------------------------------


def test_execute_triggers_approval(hook):
    assert hook._needs_approval("execute", {}) is True


def test_run_triggers_approval(hook):
    assert hook._needs_approval("run", {}) is True


# ---------------------------------------------------------------------------
# Unknown tool must NOT trigger approval
# ---------------------------------------------------------------------------


def test_unknown_tool_does_not_trigger_approval(hook):
    assert hook._needs_approval("some_random_tool", {}) is False
