# Hermes Grok Tools Setup

If the user gives this repository URL and asks Claude Code to set it up, clone the repo and run:

macOS / Linux:

```bash
./install.sh
```

Windows native PowerShell:

```powershell
.\install.ps1
```

The installer detects Claude Code and installs `hermes-grok-tools` through the Claude Code plugin marketplace. It removes old direct `claude mcp add hermes-grok` registrations if present.

If auto-detection fails, run:

```bash
./install.sh --target claude-code
```

Windows native:

```powershell
.\install.ps1 -Target claude-code
```

OAuth is user-scoped through Hermes. The plugin never stores or ships user credentials.
