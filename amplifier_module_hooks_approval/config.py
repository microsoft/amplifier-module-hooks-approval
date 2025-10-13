"""Configuration and rule matching for approval hook."""

import re
from typing import Any

# Default rules if none provided
DEFAULT_RULES = [
    {"pattern": "ls*", "action": "auto_approve", "description": "List files is safe"},
    {"pattern": "pwd", "action": "auto_approve", "description": "Print working directory is safe"},
    {"pattern": "echo*", "action": "auto_approve", "description": "Echo is safe"},
]


def check_auto_action(rules: list[dict[str, Any]], tool_name: str, arguments: dict[str, Any]) -> str | None:
    """
    Check if tool matches auto-approval rules.

    Args:
        rules: List of rule dictionaries
        tool_name: Name of the tool
        arguments: Tool arguments

    Returns:
        Action string ("auto_approve", "auto_deny") or None
    """
    # For bash tool, check command patterns
    if tool_name == "bash":
        command = arguments.get("command", "")

        for rule in rules:
            pattern = rule.get("pattern", "")
            action = rule.get("action")

            if not pattern or not action:
                continue

            # Convert simple glob pattern to regex
            if "*" in pattern:
                regex_pattern = pattern.replace("*", ".*")
            else:
                regex_pattern = f"^{re.escape(pattern)}$"

            # Check if command matches
            if re.match(regex_pattern, command, re.IGNORECASE):
                return action

    return None
