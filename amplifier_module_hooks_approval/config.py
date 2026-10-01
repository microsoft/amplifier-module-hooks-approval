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
    tokens = pattern.lstrip().split(maxsplit=1)
    return bool(tokens) and "*" not in tokens[0]


def _matches_pattern(command: str, pattern: str) -> bool:
    """Match a fully anchored pattern where only asterisks are wildcards."""
    regex_pattern = re.escape(pattern).replace(r"\*", ".*")
    return re.fullmatch(regex_pattern, command, re.IGNORECASE | re.DOTALL) is not None


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
        if not isinstance(command, str) or not command.strip():
            return None

        for rule in rules:
            if not isinstance(rule, dict):
                continue

            pattern = rule.get("pattern", "")
            action = rule.get("action")

            if not isinstance(pattern, str) or not pattern.strip() or not action:
                continue

            if _matches_pattern(command, pattern):
                if action == "auto_approve" and (
                    not _is_simple_shell_command(command)
                    or not _has_literal_executable(pattern)
                ):
                    continue
                return action

    return None
