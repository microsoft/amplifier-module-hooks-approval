"""
Approval hook module for Amplifier.
Coordinates user approval requests via pluggable providers.
"""

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

    # Create approval hook instance
    approval_hook = ApprovalHook(config)

    # Get hooks registry from coordinator
    hooks: HookRegistry = coordinator.get("hooks")
    if not hooks:
        logger.error("No hooks registry available")
        return None

    # Register for tool:pre events with high priority (runs early)
    unregister = hooks.register(
        "tool:pre",
        approval_hook.handle_tool_pre,
        priority=-10,  # Negative = high priority
        name="approval_hook",
    )

    # Mount the approval hook itself in a dedicated mount point for access by app layer
    # App layer can use coordinator.get("hooks").get_handler("approval_hook") to access it
    logger.info("Mounted ApprovalHook")

    # Return cleanup function
    def cleanup():
        unregister()
        logger.info("Unmounted ApprovalHook")

    return cleanup
