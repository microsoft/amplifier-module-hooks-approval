# Amplifier Approval Hook Module

Intercepts tool execution requests and coordinates user approval before dangerous operations.

## Features

- Hook-based interception via `tool:pre` events
- Pluggable approval providers (CLI, GUI, headless)
- Rule-based auto-approval configuration
- Audit trail logging (JSONL format)
- Risk-level based approval requirements
- Optional timeout support

## Configuration

```toml
[[hooks]]
module = "hooks-approval"

[hooks.approval]
default_action = "deny"  # Action on timeout/error

[[hooks.approval.rules]]
pattern = "ls*"
action = "auto_approve"

[[hooks.approval.rules]]
pattern = "rm -rf /*"
action = "auto_deny"
```

## Documentation

- **[Usage Guide](USAGE_GUIDE.md)** - Complete guide with examples and troubleshooting
- **[Configuration Example](config.example.toml)** - Sample configuration file
- **[Implementation Plan](../../ai_working/amplifier-v2/IMPLEMENTATION_PLAN.md)** - Full implementation details

## Philosophy

- Mechanism, not policy: Core provides hooks, this module orchestrates
- Tools declare needs via metadata
- Providers handle UI
- Audit trail for accountability

## Testing

```bash
# Unit tests
python -m pytest tests/ -v

# Integration tests
cd ../.. && python test_integration.py

# Smoke test
cd ../.. && python smoke_test_approval.py
```

## Quick Start

See [USAGE_GUIDE.md](USAGE_GUIDE.md) for complete documentation.