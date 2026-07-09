# Codex Adapter

Use this adapter when the setup request is made from Codex.

```bash
./install.sh --target codex
```

This installs `hermes-grok-tools` through the Codex plugin marketplace flow.
It does not use `codex mcp add`, and it does not modify Claude Code, Cursor,
or Antigravity settings.

When using the generation tools, ask for missing output/cost settings before
calling MCP tools. Use `request_user_input` when available. Ask for quality and
aspect ratio for images; quality, duration seconds, and aspect ratio for video
generation; quality for video edit; quality and extension seconds for video
extend. Do not ask non-technical users to choose raw model IDs. Pass
`confirmed_settings: true` after the user supplies, approves, or delegates those
settings.
