"""Configuration and rule matching for approval hook."""

import re
from typing import Any

# Default rules if none provided
DEFAULT_RULES = [
    {"pattern": "ls", "action": "auto_approve", "description": "List files is safe"},
    {"pattern": "ls *", "action": "auto_approve", "description": "List files is safe"},
    {
        "pattern": "pwd",
        "action": "auto_approve",
        "description": "Print working directory is safe",
    },
    {"pattern": "echo", "action": "auto_approve", "description": "Echo is safe"},
    {"pattern": "echo *", "action": "auto_approve", "description": "Echo is safe"},
]

_SHELL_CONTROL_CHARACTERS = frozenset(";&|<>\r\n`$()\\")


def _is_simple_shell_command(command: Any) -> bool:
    """Return whether a command is safe to evaluate against auto-action rules."""
    if not isinstance(command, str) or not command.strip():
        return False

    return not any(character in command for character in _SHELL_CONTROL_CHARACTERS)


def _has_literal_executable(pattern: str) -> bool:
    """Require rules to name the executable rather than globbing its name."""
    executable_pattern = pattern.lstrip().split(maxsplit=1)[0]
    return "*" not in executable_pattern


def _matches_pattern(command: str, pattern: str) -> bool:
    """Match a fully anchored pattern where only asterisks are wildcards."""
    regex_pattern = re.escape(pattern).replace(r"\*", ".*")
    return re.fullmatch(regex_pattern, command, re.IGNORECASE) is not None


def check_auto_action(
    rules: list[dict[str, Any]], tool_name: str, arguments: dict[str, Any]
) -> str | None:
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
        if not _is_simple_shell_command(command):
            return None

        for rule in rules:
            pattern = rule.get("pattern", "")
            action = rule.get("action")

            if (
                not isinstance(pattern, str)
                or not pattern
                or not action
                or not _has_literal_executable(pattern)
            ):
                continue

            if _matches_pattern(command, pattern):
                return action

    return None
