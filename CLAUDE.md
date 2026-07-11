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

Grok 4.5 defaults to `high` reasoning effort. Before media generation, use Claude Code's structured AskUserQuestion UI for missing settings. Confirm image quality/model, resolution, and aspect ratio; confirm video quality, 480p/720p resolution, 6/10-second duration, and aspect ratio. Pass `confirmed_settings: true` only after the user supplies, approves, or delegates them. Do not repeat settings already provided. Grok CLI creates a source image before animation when needed.

Relay every successful Grok `answer` verbatim. Do not summarize, paraphrase, translate, reorder, correct, or silently truncate it. Preserve Markdown, code blocks, links, language, and line breaks. Reply with only Grok's answer by default. Put unavoidable Claude Code commentary after the complete answer under a separate `Host agent note` heading. Preserve generated media paths and URLs exactly.

When a tool returns `error_type: usage_limit`, show the complete error and both clickable recovery links for SuperGrok and X Premium/Premium+ without rewriting or removing them. Do not mention Extra Usage Credits. Preserve the original Grok CLI error. Do not retry automatically or silently lower reasoning effort.

If the user upgraded or changed plans after the current CLI login, or shows an active paid plan with remaining usage, run `grok logout` and then `grok login` in the host terminal before recommending another purchase. Tell the user to complete browser or device-code authentication, then retry the original Grok request once. Do not log out solely because of an ambiguous 429.

If the retry still returns the same usage limit, tell the user to fully quit and restart Claude Code, then retry once when the conversation resumes. Never automatically terminate or relaunch the host because the active agent cannot reliably continue afterward.

Repository inspection stays read-only; only generated media files may be created through Grok Build's bundled Imagine tools. This plugin does not claim dedicated X Search.
