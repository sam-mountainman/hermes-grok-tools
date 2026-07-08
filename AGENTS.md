# Hermes Grok Tools Setup

When a user gives this repository URL and asks to set it up, install the plugin for the current AI agent host.

Default command:

macOS / Linux:

```bash
./install.sh
```

Windows native PowerShell:

```powershell
.\install.ps1
```

`install.sh` auto-detects Codex, Claude Code, Cursor, Antigravity, or Gemini when the host exposes enough environment context. If auto-detection fails, rerun with one explicit target:

```bash
./install.sh --target codex
./install.sh --target claude-code
./install.sh --target cursor
./install.sh --target antigravity
./install.sh --target gemini
```

On Windows native, use:

```powershell
.\install.ps1 -Target codex
.\install.ps1 -Target claude-code
.\install.ps1 -Target cursor
.\install.ps1 -Target antigravity
.\install.ps1 -Target gemini
```

Do not install this as a bare MCP server unless the user explicitly asks for a fallback. The normal path is a host-native plugin or extension:

- Codex: Codex plugin marketplace.
- Claude Code: Claude Code plugin marketplace.
- Cursor: local Cursor plugin, plus Team Marketplace support from the GitHub repo.
- Antigravity/Gemini: Gemini-compatible extension/plugin.

Hermes xAI/Grok OAuth is per-user. If the installer starts `hermes auth add xai-oauth`, browser/device login may require the user's action.

On Windows, do not ask the user to install WSL. `install.ps1` uses Hermes Agent's native Windows installer and creates a `python3.cmd` shim for MCP hosts.
