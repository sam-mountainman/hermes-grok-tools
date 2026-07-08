# Hermes Grok Tools Setup

When a user gives this repository URL and asks to set it up, install the plugin for the current AI agent host.

Default command:

```bash
./install.sh
```

`install.sh` auto-detects Codex, Claude Code, Cursor, Antigravity, or Gemini when the host exposes enough environment context. If auto-detection fails, rerun with one explicit target:

```bash
./install.sh --target codex
./install.sh --target claude-code
./install.sh --target cursor
./install.sh --target antigravity
./install.sh --target gemini
```

Do not install this as a bare MCP server unless the user explicitly asks for a fallback. The normal path is a host-native plugin or extension:

- Codex: Codex plugin marketplace.
- Claude Code: Claude Code plugin marketplace.
- Cursor: local Cursor plugin, plus Team Marketplace support from the GitHub repo.
- Antigravity/Gemini: Gemini-compatible extension/plugin.

Hermes xAI/Grok OAuth is per-user. If the installer starts `hermes auth add xai-oauth`, browser/device login may require the user's action.
