# Hermes Grok Tools

Use the `hermes-grok` MCP server when the user asks for Hermes Agent Grok OAuth X search, Grok image generation, or Grok video generation.

Before generation-heavy work, call `hermes_grok_status` to confirm Hermes, provider configuration, and xAI OAuth credentials are available.

When the user gives this repository URL and asks Gemini or Antigravity-compatible hosts to set it up, clone the repo and run:

macOS / Linux:

```bash
./install.sh
```

Windows native PowerShell:

```powershell
.\install.ps1
```

If auto-detection fails, run:

```bash
./install.sh --target gemini
```

Windows native:

```powershell
.\install.ps1 -Target gemini
```

OAuth is user-scoped through Hermes. The plugin never stores or ships user credentials.

The installer sets default lower-cost Imagine models: `grok-imagine-image` for images and `grok-imagine-video` for videos. The plugin tools accept `quality`: `standard` keeps those defaults, while `quality` / `high` / `high_quality` selects `grok-imagine-image-quality` or `grok-imagine-video-1.5`. `grok-imagine-video-1.5` needs image/video input and should not be used for text-only video generation.
