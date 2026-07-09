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

The installer sets default lower-cost Imagine models: `grok-imagine-image` for images and `grok-imagine-video` for videos. The plugin tools accept `quality`: `standard` keeps those defaults, while `quality` / `high` / `high_quality` selects `grok-imagine-image-quality` or `grok-imagine-video-1.5`. `grok-imagine-video-1.5` needs image/video input and should not be used for text-only video generation.

Before calling image/video generation tools, ask only for missing settings that affect output or cost. Use structured AskUserQuestion UI when Claude Code supports it; otherwise ask a concise text fallback. Do not ask users to choose raw model IDs. Ask for quality and aspect ratio for images; quality, duration seconds, and aspect ratio for video generation; quality for video edit; quality and extension seconds for video extend. If the user already specified the settings or says to choose automatically, call the tool with `confirmed_settings: true` and sensible defaults.
