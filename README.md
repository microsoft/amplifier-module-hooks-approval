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

## Contributing

> [!NOTE]
> This project is not currently accepting external contributions, but we're actively working toward opening this up. We value community input and look forward to collaborating in the future. For now, feel free to fork and experiment!

Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit [Contributor License Agreements](https://cla.opensource.microsoft.com).

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft
trademarks or logos is subject to and must follow
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
