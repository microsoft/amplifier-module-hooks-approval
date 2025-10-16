# Amplifier Approval Hook Module

Intercepts tool execution requests and coordinates user approval before dangerous operations.

## Prerequisites

- **Python 3.11+**
- **[UV](https://github.com/astral-sh/uv)** - Fast Python package manager

### Installing UV

```bash
# macOS/Linux/WSL
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```
## Features

- Hook-based interception via `tool:pre` events
- Pluggable approval providers (CLI, GUI, headless)
- Rule-based auto-approval configuration
- Audit trail logging (JSONL format)
- Risk-level based approval requirements
- Optional timeout support

## Configuration

Configure in your profile (see [PROFILE_AUTHORING.md](../../docs/PROFILE_AUTHORING.md)):

```yaml
# In your profile .md file
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

**Working example:** See `amplifier-app-cli/amplifier_app_cli/data/profiles/full.md`

## Documentation

- **[Usage Guide](USAGE_GUIDE.md)** - Complete guide with examples and troubleshooting
- **[Profile Authoring Guide](../../docs/PROFILE_AUTHORING.md)** - How to configure hooks in profiles

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