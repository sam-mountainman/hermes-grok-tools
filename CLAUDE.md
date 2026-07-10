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

Use `grok_status` for setup checks. Use `grok_ask`, `grok_research`, `grok_plan`, or `grok_review` when the user explicitly requests Grok/Grok 4.5 or a Grok second opinion. Use `grok_generate_image` and `grok_generate_video` for explicit Grok Imagine requests. Continue a conversation with the returned `session_id`. Do not call Grok automatically for every ordinary question.

Grok 4.5 defaults to `high` reasoning effort. Before media generation, use Claude Code's structured AskUserQuestion UI for missing model/quality and output settings. Confirm image quality/model, resolution, and aspect ratio; confirm video model/quality and resolution, duration, and aspect ratio. Pass `confirmed_settings: true` only after the user supplies, approves, or delegates them. Do not repeat settings already provided. Text-to-video supports 480p/720p with `grok-imagine-video`; `grok-imagine-video-1.5` and 1080p require a source image.

Repository inspection stays read-only; only generated media files may be created through Grok Build's bundled Imagine tools. This plugin does not claim dedicated X Search.
