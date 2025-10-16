# Approval Hook System - Usage Guide

## Overview

The approval hook system provides user permission prompts for dangerous tool operations in Amplifier. It follows a hook-based architecture where:

- **Core** defines minimal protocols (`ApprovalRequest`, `ApprovalResponse`, `ApprovalProvider`)
- **Hook module** orchestrates approval requests by intercepting `tool:pre` events
- **Provider implementations** handle the UI (CLI, GUI, headless)
- **Tools** declare their approval requirements via metadata

## Quick Start

### 1. Enable the Approval Hook

Add to your profile (see `amplifier-app-cli/amplifier_app_cli/data/profiles/full.md` for working example):

```yaml
---
hooks:
  - module: hooks-approval
    config:
      patterns:
        - rm -rf
        - sudo
        - dd if=
      auto_approve: false
---
```

### 2. Configure Tool Requirements

Tools declare approval needs via `get_metadata()`:

```python
def get_metadata(self) -> dict[str, Any]:
    return {
        "requires_approval": True,
        "approval_hints": {
            "risk_level": "high",
            "dangerous_patterns": ["rm -rf /", "sudo rm"],
            "safe_patterns": ["ls", "pwd"]
        }
    }
```

### 3. Register an Approval Provider

In your CLI application:

```python
from amplifier_app_cli.approval_provider import CLIApprovalProvider

# Create provider
console = Console()
provider = CLIApprovalProvider(console)

# Register with approval hook
coordinator._approval_hook.register_provider(provider)
```

## Configuration Options

### Hook Configuration

Configure via your profile's hooks section:

```yaml
hooks:
  - module: hooks-approval
    config:
      # Dangerous command patterns that always require approval
      patterns:
        - rm -rf
        - sudo
        - dd if=
        - mkfs
        - iptables

      # Auto-approve mode (use with caution)
      auto_approve: false

      # Default action on timeout/error
      default_action: deny  # or "continue"
```

**Note:** The module currently supports pattern-based blocking. Rule-based auto-approval is planned for future versions.

### Rule Matching Priority

Rules are evaluated in order:
1. Exact tool + command pattern match
2. Tool name match
3. Risk level match
4. Default behavior (check metadata)

## Approval Request Flow

```
User Action
    ↓
Tool Execution Request
    ↓
Orchestrator emits tool:pre event
    ↓
Approval Hook intercepts
    ↓
Check rules & metadata
    ↓
    ├─ Safe command → Continue (no prompt)
    ├─ Auto-approve rule → Continue
    ├─ Auto-deny rule → Deny
    └─ Needs approval → Request from provider
                           ↓
                    Provider shows UI
                           ↓
                    User decides (y/n)
                           ↓
                    Provider returns response
                           ↓
                    Hook logs to audit trail
                           ↓
                    Hook returns continue/deny
                           ↓
                    Orchestrator executes or skips tool
```

## Timeout Behavior

The approval system supports optional timeouts:

```python
request = ApprovalRequest(
    tool_name="bash",
    action="rm logs/*.log",
    details={"command": "rm logs/*.log"},
    risk_level="high",
    timeout=None  # Wait forever (default)
    # timeout=30.0  # Or timeout after 30 seconds
)
```

**Default: No timeout** - The system waits indefinitely for user response (common case for unattended operations).

**Optional timeout** - Set a positive float for edge cases (CI/CD pipelines, batch jobs, hung provider recovery).

**On timeout**:
- Hook uses `default_action` from config (typically "deny")
- Event is logged to audit trail

## Audit Trail

When enabled, all approval decisions are logged to a JSONL file:

```json
{"timestamp": "2025-10-07T12:34:56Z", "tool": "bash", "action": "rm test.txt", "risk_level": "high", "approved": true, "reason": "User approved"}
{"timestamp": "2025-10-07T12:35:01Z", "tool": "bash", "action": "rm -rf /", "risk_level": "critical", "approved": false, "reason": "Auto-deny rule"}
```

## Creating Custom Approval Providers

Implement the `ApprovalProvider` protocol:

```python
from amplifier_core import ApprovalProvider, ApprovalRequest, ApprovalResponse

class MyCustomProvider:
    async def request_approval(self, request: ApprovalRequest) -> ApprovalResponse:
        # Show your custom UI
        # Get user decision
        # Return response
        return ApprovalResponse(
            approved=user_decision,
            reason="User approved" if user_decision else "User denied"
        )
```

Then register with the approval hook:

```python
coordinator._approval_hook.register_provider(my_provider)
```

## Example: CLI Approval Provider

The included CLI provider shows a Rich panel:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ⚠️  Approval Required                ┃
┃                                       ┃
┃ Tool: bash                            ┃
┃ Action: rm logs/*.log                 ┃
┃ Risk Level: HIGH                      ┃
┃                                       ┃
┃ Details:                              ┃
┃   command: rm logs/*.log              ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Approve this action? [y/n]:
```

## Testing

### Unit Tests

```bash
cd amplifier-module-hooks-approval
python -m pytest tests/ -v
```

## Philosophy Compliance

This system follows Amplifier's kernel philosophy:

- **Mechanism, not policy**: Core defines protocols only; modules implement behavior
- **Stable contracts**: No breaking changes to existing interfaces
- **Small core**: Only 3 protocol classes in core; all logic in modules
- **Separation of concerns**: Tools declare needs, Hook orchestrates, Provider handles UI
- **Optional timeout = mechanism**: Default `None` (wait forever); callers control their fate

## Benefits

✅ Zero breaking changes - Core business logic unchanged
✅ Backward compatible - Tools work without approval hook
✅ Multiple UIs supported - CLI, GUI, headless can provide approvals
✅ Flexible timeout behavior - Default (wait forever) handles common case
✅ Auditable - All decisions logged in structured format
✅ Configurable - Rules-based auto-approval possible
✅ Kernel compliant - Mechanism in core, policy in modules

## Troubleshooting

### Provider not receiving requests

Check that:
1. Approval hook is mounted: `coordinator.get("hooks")`
2. Provider is registered: `coordinator._approval_hook.register_provider(provider)`
3. Tool metadata declares `requires_approval: True`

### All requests auto-approve

Check:
1. Config rules aren't set to `auto_approve` for everything
2. Tool's `get_metadata()` is returning correct `requires_approval` flag
3. Commands aren't matching safe patterns unintentionally

### Audit trail not logging

Check:
1. Config has `[hooks.approval.audit] enabled = true`
2. File path is writable
3. Directory exists

## Next Steps

- Add custom approval providers for your UI
- Configure auto-approval rules for trusted commands
- Monitor audit trail for security analysis
- Extend to other tools beyond bash
