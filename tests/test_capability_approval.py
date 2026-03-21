"""Tests for approval.needs_check capability callback integration.

Tests the approval hook's use of get_capability("approval.needs_check")
instead of session_state to determine if a tool needs approval.
"""

from unittest.mock import MagicMock

from amplifier_module_hooks_approval.approval_hook import ApprovalHook


class TestCapabilityApproval:
    """Tests for approval hook using approval.needs_check capability callback."""

    def _make_coordinator(self, callback=None):
        """Create a mock coordinator with optional needs_check capability."""
        coordinator = MagicMock()
        coordinator.get_capability.return_value = callback
        return coordinator

    def test_callback_returns_true_triggers_approval(self):
        """When the callback returns True for a tool, approval should be required."""

        def needs_check_callback(tool_name):
            return tool_name == "some_tool"

        coordinator = self._make_coordinator(callback=needs_check_callback)

        hook = ApprovalHook(
            config={"policy_driven_only": True},
            coordinator=coordinator,
        )

        result = hook._needs_approval("some_tool", {})

        # Verify coordinator was asked for the capability
        coordinator.get_capability.assert_called_with("approval.needs_check")
        # Approval should be required
        assert result is True

    def test_callback_returns_false_no_approval(self):
        """When the callback returns False for a tool, no approval should be triggered."""

        def needs_check_callback(tool_name):
            return False

        coordinator = self._make_coordinator(callback=needs_check_callback)

        hook = ApprovalHook(
            config={"policy_driven_only": True},
            coordinator=coordinator,
        )

        result = hook._needs_approval("safe_tool", {})

        # Verify coordinator was asked for the capability
        coordinator.get_capability.assert_called_with("approval.needs_check")
        # No approval needed since policy_driven_only=True and callback returned False
        assert result is False

    def test_no_callback_registered_falls_through(self):
        """When no callback is registered (None), falls through gracefully (no approval from callback)."""
        # No callback registered - get_capability returns None
        coordinator = self._make_coordinator(callback=None)

        hook = ApprovalHook(
            config={"policy_driven_only": True},
            coordinator=coordinator,
        )

        result = hook._needs_approval("any_tool", {})

        # Verify coordinator was asked for the capability
        coordinator.get_capability.assert_called_with("approval.needs_check")
        # No callback registered, and policy_driven_only means no built-in checks
        # Should return False (falls through gracefully)
        assert result is False

    def test_policy_driven_only_with_callback(self):
        """When policy_driven_only=True and callback returns True, approval is triggered.

        The capability callback should take precedence over policy_driven_only bypass —
        the callback IS the policy driver.
        """

        def needs_check_callback(tool_name):
            return tool_name == "controlled_tool"

        coordinator = self._make_coordinator(callback=needs_check_callback)

        hook = ApprovalHook(
            config={"policy_driven_only": True},
            coordinator=coordinator,
        )

        # With callback returning True, approval should be required
        assert hook._needs_approval("controlled_tool", {}) is True

        # With callback returning False, no approval (policy_driven_only, no built-in checks)
        assert hook._needs_approval("other_tool", {}) is False
