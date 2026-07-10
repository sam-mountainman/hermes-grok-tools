# Grok CLI Tools Setup

When the user gives this repository URL and asks Claude Code to set it up, clone the repository and run:

```bash
./install.sh --target claude-code
```

Windows native PowerShell:

```powershell
.\install.ps1 -Target claude-code
```

The installer installs the official Grok CLI if needed, starts `grok login`, and installs only the Claude Code plugin. It removes an old `hermes-grok-tools` registration during migration and does not modify Codex, Cursor, Antigravity, or Gemini settings.

Use `grok_status` for setup checks. Use `grok_ask`, `grok_research`, `grok_plan`, or `grok_review` when the user explicitly requests Grok/Grok 4.5 or a Grok second opinion. Continue a conversation with the returned `session_id`. Do not call Grok automatically for every ordinary question.

Grok runs read-only. This plugin provides general questions, Web research, planning, and review; it does not claim dedicated X Search, image generation, or video generation through Grok CLI.
