"""
Approval hook module for Amplifier.
Coordinates user approval requests via pluggable providers.
"""

# Amplifier module metadata
__amplifier_module_type__ = "hook"

import logging
from typing import Any

from amplifier_core import HookRegistry
from amplifier_core import ModuleCoordinator

from .approval_hook import ApprovalHook

logger = logging.getLogger(__name__)


async def mount(coordinator: ModuleCoordinator, config: dict[str, Any] | None = None):
    """
    Mount the approval hook module.

    Args:
        coordinator: Module coordinator
        config: Hook configuration

    Returns:
        Optional cleanup function
    """
    config = config or {}

    # Get hooks registry from coordinator
    hooks: HookRegistry = coordinator.get("hooks")
    if not hooks:
        logger.error("No hooks registry available")
        return None

    # Create approval hook instance with hooks registry for event emission
    approval_hook = ApprovalHook(config, hooks=hooks)

    # Register for tool:pre events with high priority (runs early)
    unregister = hooks.register(
        "tool:pre",
        approval_hook.handle_tool_pre,
        priority=-10,  # Negative = high priority
        name="approval_hook",
    )

    # Register capability for app layer to register providers
    coordinator.register_capability("approval.register_provider", approval_hook.register_provider)

    logger.info("Mounted ApprovalHook")

    # Return cleanup function
    def cleanup():
        unregister()
        logger.info("Unmounted ApprovalHook")

    return cleanup
