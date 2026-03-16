"""Tests for PR6: remember field in ApprovalResponse.

Verifies that when response.remember=True the decision is stored and
replayed on subsequent calls without prompting the provider again.
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from amplifier_core import ApprovalResponse
from amplifier_module_hooks_approval.approval_hook import ApprovalHook

# Minimal config that disables audit (no filesystem writes during tests)
_CFG = {"audit": {"enabled": False}}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_hook():
    return ApprovalHook(config=_CFG)


def make_provider(approved: bool, remember: bool = False, reason: str = "ok") -> AsyncMock:
    """Return a mock ApprovalProvider whose request_approval is an AsyncMock."""
    response = ApprovalResponse(approved=approved, reason=reason, remember=remember)
    provider = MagicMock()
    provider.request_approval = AsyncMock(return_value=response)
    return provider


async def call_tool(hook, tool_name, tool_input):
    return await hook.handle_tool_pre("tool:pre", {"tool_name": tool_name, "tool_input": tool_input})


# ---------------------------------------------------------------------------
# Instance structure
# ---------------------------------------------------------------------------


def test_remembered_decisions_starts_empty():
    """_remembered_decisions must be an empty dict on a fresh instance."""
    hook = make_hook()
    assert isinstance(hook._remembered_decisions, dict)
    assert len(hook._remembered_decisions) == 0


def test_remembered_decisions_is_dict_on_instance():
    hook = make_hook()
    assert hasattr(hook, "_remembered_decisions")
    assert isinstance(hook._remembered_decisions, dict)


# ---------------------------------------------------------------------------
# _build_remember_key
# ---------------------------------------------------------------------------


def test_build_remember_key_filesystem_write_file():
    hook = make_hook()
    key = hook._build_remember_key("write_file", {"file_path": "src/foo.py"})
    assert key == "write_file:src"


def test_build_remember_key_filesystem_edit_file():
    hook = make_hook()
    key = hook._build_remember_key("edit_file", {"file_path": "src/bar.py"})
    assert key == "edit_file:src"


def test_build_remember_key_filesystem_root_path():
    hook = make_hook()
    key = hook._build_remember_key("write_file", {"file_path": ".env"})
    assert key == "write_file:."


def test_build_remember_key_bash_two_words():
    hook = make_hook()
    key = hook._build_remember_key("bash", {"command": "git push origin main"})
    assert key == "bash:git push"


def test_build_remember_key_bash_one_word():
    hook = make_hook()
    key = hook._build_remember_key("bash", {"command": "ls"})
    assert key == "bash:ls"


def test_build_remember_key_bash_empty_command():
    hook = make_hook()
    key = hook._build_remember_key("bash", {"command": ""})
    assert key == "bash:"


def test_build_remember_key_other_tool():
    hook = make_hook()
    key = hook._build_remember_key("execute", {})
    assert key == "execute"


def test_build_remember_key_no_path_falls_back_to_tool_name():
    """When file_path is absent the key falls back to just the tool name."""
    hook = make_hook()
    key = hook._build_remember_key("write_file", {})
    assert key == "write_file"


# ---------------------------------------------------------------------------
# remember=False must NOT store anything
# ---------------------------------------------------------------------------


def test_remember_false_does_not_store():
    hook = make_hook()
    hook.register_provider(make_provider(approved=True, remember=False))
    asyncio.run(call_tool(hook, "write_file", {"file_path": "src/x.py"}))
    assert len(hook._remembered_decisions) == 0


# ---------------------------------------------------------------------------
# Remembered approval skips provider on subsequent calls
# ---------------------------------------------------------------------------


def test_remembered_approval_skips_future_prompts():
    hook = make_hook()
    provider = make_provider(approved=True, remember=True)
    hook.register_provider(provider)

    # First call: provider is invoked, decision stored
    result1 = asyncio.run(call_tool(hook, "write_file", {"file_path": "src/a.py"}))
    assert result1.action == "continue"
    assert provider.request_approval.call_count == 1

    # Second call for same directory: provider must NOT be called again
    result2 = asyncio.run(call_tool(hook, "write_file", {"file_path": "src/b.py"}))
    assert result2.action == "continue"
    assert provider.request_approval.call_count == 1  # unchanged


def test_remembered_approval_for_one_dir_does_not_cover_other_dir():
    """Approving src/ must NOT auto-approve writes to .env (parent '.')."""
    hook = make_hook()
    provider = make_provider(approved=True, remember=True)
    hook.register_provider(provider)

    # Approve src/
    asyncio.run(call_tool(hook, "write_file", {"file_path": "src/a.py"}))
    assert provider.request_approval.call_count == 1

    # .env lives in '.', a different scope — provider must be called again
    asyncio.run(call_tool(hook, "write_file", {"file_path": ".env"}))
    assert provider.request_approval.call_count == 2


def test_remembered_bash_approval_does_not_cover_different_prefix():
    """Approving 'git push' must NOT auto-approve 'rm -rf'."""
    hook = make_hook()
    provider = make_provider(approved=True, remember=True)
    hook.register_provider(provider)

    asyncio.run(call_tool(hook, "bash", {"command": "git push origin main"}))
    assert provider.request_approval.call_count == 1

    asyncio.run(call_tool(hook, "bash", {"command": "rm -rf /tmp/foo"}))
    assert provider.request_approval.call_count == 2


# ---------------------------------------------------------------------------
# Remembered denial blocks future calls
# ---------------------------------------------------------------------------


def test_remembered_denial_blocks_future_calls():
    hook = make_hook()
    provider = make_provider(approved=False, remember=True, reason="no writes")
    hook.register_provider(provider)

    result1 = asyncio.run(call_tool(hook, "write_file", {"file_path": "src/a.py"}))
    assert result1.action == "deny"
    assert provider.request_approval.call_count == 1

    result2 = asyncio.run(call_tool(hook, "write_file", {"file_path": "src/b.py"}))
    assert result2.action == "deny"
    assert "remembered" in result2.reason.lower()
    assert provider.request_approval.call_count == 1  # provider not called again


# ---------------------------------------------------------------------------
# Different tool names have separate keys
# ---------------------------------------------------------------------------


def test_different_tool_names_have_separate_keys():
    hook = make_hook()
    provider_w = make_provider(approved=True, remember=True)
    hook.register_provider(provider_w)

    # Approve write_file for src/
    asyncio.run(call_tool(hook, "write_file", {"file_path": "src/a.py"}))
    # edit_file for src/ is a DIFFERENT key — must still hit provider
    asyncio.run(call_tool(hook, "edit_file", {"file_path": "src/b.py"}))
    assert provider_w.request_approval.call_count == 2


# ---------------------------------------------------------------------------
# Non-remembered approvals still require re-prompting
# ---------------------------------------------------------------------------


def test_non_remembered_approval_re_prompts():
    hook = make_hook()
    provider = make_provider(approved=True, remember=False)
    hook.register_provider(provider)

    asyncio.run(call_tool(hook, "write_file", {"file_path": "src/a.py"}))
    asyncio.run(call_tool(hook, "write_file", {"file_path": "src/b.py"}))
    # Provider must have been called for each request
    assert provider.request_approval.call_count == 2


# ---------------------------------------------------------------------------
# Resetting remembered decisions
# ---------------------------------------------------------------------------


def test_clearing_remembered_decisions_re_prompts():
    hook = make_hook()
    provider = make_provider(approved=True, remember=True)
    hook.register_provider(provider)

    asyncio.run(call_tool(hook, "write_file", {"file_path": "src/a.py"}))
    assert provider.request_approval.call_count == 1

    # Clear remembered decisions
    hook._remembered_decisions.clear()

    asyncio.run(call_tool(hook, "write_file", {"file_path": "src/b.py"}))
    assert provider.request_approval.call_count == 2


def test_new_hook_instance_has_no_remembered_decisions():
    """Each new ApprovalHook starts with a fresh empty remember dict."""
    hook1 = make_hook()
    hook2 = make_hook()
    provider = make_provider(approved=True, remember=True)
    hook1.register_provider(provider)

    asyncio.run(call_tool(hook1, "write_file", {"file_path": "src/a.py"}))
    assert len(hook1._remembered_decisions) == 1
    # hook2 is completely independent
    assert len(hook2._remembered_decisions) == 0
