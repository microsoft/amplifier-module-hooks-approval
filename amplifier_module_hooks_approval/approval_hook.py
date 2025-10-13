"""Core approval hook logic."""

import asyncio
import logging
from typing import Any

from amplifier_core import ApprovalProvider
from amplifier_core import ApprovalRequest
from amplifier_core import ApprovalResponse
from amplifier_core import HookResult

from .audit import audit_log
from .config import DEFAULT_RULES
from .config import check_auto_action

logger = logging.getLogger(__name__)


class ApprovalHook:
    """
    Approval hook that intercepts tool executions and requests user approval.

    Responsibilities:
    - Check if tool needs approval
    - Call registered approval provider
    - Return deny/continue based on response
    - Log all decisions to audit trail
    """

    def __init__(self, config: dict[str, Any]):
        """Initialize approval hook with configuration."""
        self.config = config
        self.provider: ApprovalProvider | None = None
        self.rules = config.get("rules", DEFAULT_RULES)
        self.default_action = config.get("default_action", "deny")
        self.audit_enabled = config.get("audit", {}).get("enabled", True)

        logger.debug(f"ApprovalHook initialized with {len(self.rules)} rules")

    def register_provider(self, provider: ApprovalProvider) -> None:
        """
        Register an approval provider (e.g., CLI, GUI).

        Args:
            provider: Approval provider implementing ApprovalProvider protocol
        """
        self.provider = provider
        logger.info(f"Registered approval provider: {provider.__class__.__name__}")

    async def handle_tool_pre(self, event: str, data: dict[str, Any]) -> HookResult:
        """
        Handle tool:pre event and request approval if needed.

        Args:
            event: Event name ("tool:pre")
            data: Event data with 'tool', 'arguments', and optionally 'tool_obj'

        Returns:
            HookResult with continue or deny action
        """
        tool_name = data.get("tool", "unknown")
        arguments = data.get("arguments", {})
        tool_obj = data.get("tool_obj")  # Tool object if provided by orchestrator

        # Check if needs approval
        if not self._needs_approval(tool_name, arguments, tool_obj):
            return HookResult(action="continue")

        # Build approval request
        request = self._build_request(tool_name, arguments)

        # Check for auto-action rules first
        auto_action = check_auto_action(self.rules, tool_name, arguments)
        if auto_action:
            logger.info(f"Auto-action '{auto_action}' for {tool_name}")

            # Log to audit trail
            if self.audit_enabled:
                response = ApprovalResponse(
                    approved=(auto_action == "auto_approve"), reason=f"Auto-action: {auto_action}"
                )
                audit_log(request, response)

            if auto_action == "auto_approve":
                return HookResult(action="continue")
            # auto_deny
            return HookResult(action="deny", reason="Auto-denied by rule")

        # Request approval from provider
        try:
            response = await self._request_approval(request)

            # Log decision
            if self.audit_enabled:
                audit_log(request, response)

            # Return hook result
            if response.approved:
                return HookResult(action="continue")
            return HookResult(action="deny", reason=response.reason or "User denied approval")

        except TimeoutError:
            # Timeout expired - use default action
            logger.warning(f"Approval timeout for {tool_name}, using default: {self.default_action}")

            if self.audit_enabled:
                response = ApprovalResponse(approved=False, reason="Approval request timed out")
                audit_log(request, response)

            return HookResult(action=self.default_action, reason="Approval request timed out")

        except Exception as e:
            # Provider error - fail safe (deny)
            logger.error(f"Approval provider error: {e}", exc_info=True)

            if self.audit_enabled:
                response = ApprovalResponse(approved=False, reason=f"Provider error: {str(e)}")
                audit_log(request, response)

            return HookResult(action="deny", reason=f"Approval system error: {e}")

    def _needs_approval(self, tool_name: str, arguments: dict[str, Any], tool_obj: Any = None) -> bool:
        """
        Check if tool execution needs approval.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            tool_obj: Tool object (optional) to check for require_approval attribute

        Returns:
            True if approval needed
        """
        # First check if tool has require_approval attribute
        if tool_obj and hasattr(tool_obj, "require_approval") and tool_obj.require_approval:
            return True

        # Check config for tool-specific approval requirements
        tool_config = self.config.get("tools", {}).get(tool_name, {})
        if tool_config.get("require_approval", False):
            return True

        # Special handling for bash - check for dangerous patterns
        if tool_name == "bash":
            command = arguments.get("command", "")
            # Always require approval for bash unless explicitly safe
            # Check for dangerous patterns that ALWAYS need approval
            dangerous_patterns = ["rm", "sudo", "chmod", "chown", "dd", "mkfs", ">", ">>"]
            if any(pattern in command.lower() for pattern in dangerous_patterns):
                return True
            # For bash, default to requiring approval unless auto-approved by rules
            return True  # Changed: Always require approval for bash by default

        # Check if tool is in high-risk list
        high_risk_tools = ["write", "edit", "bash", "execute", "run"]
        return tool_name in high_risk_tools

    def _build_request(self, tool_name: str, arguments: dict[str, Any]) -> ApprovalRequest:
        """
        Build approval request from tool info.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments

        Returns:
            ApprovalRequest with details
        """
        # Determine action description
        if tool_name == "bash":
            action = f"Execute: {arguments.get('command', 'unknown command')}"
        else:
            action = f"Execute {tool_name}"

        # Determine risk level (simplified)
        risk_level = "high" if tool_name == "bash" else "medium"

        # Build request
        request = ApprovalRequest(
            tool_name=tool_name,
            action=action,
            details=arguments,
            risk_level=risk_level,
            timeout=self.config.get("default_timeout"),  # None by default
        )

        return request

    async def _request_approval(self, request: ApprovalRequest) -> ApprovalResponse:
        """
        Request approval from registered provider.

        Args:
            request: Approval request

        Returns:
            Approval response

        Raises:
            RuntimeError: If no provider registered
            TimeoutError: If request times out
        """
        if not self.provider:
            # No provider registered - auto-deny for safety
            logger.warning("No approval provider registered, auto-denying")
            return ApprovalResponse(approved=False, reason="No approval provider available")

        # Call provider with optional timeout
        if request.timeout is not None:
            response = await asyncio.wait_for(self.provider.request_approval(request), timeout=request.timeout)
        else:
            response = await self.provider.request_approval(request)

        return response
