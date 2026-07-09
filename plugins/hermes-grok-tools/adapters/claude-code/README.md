# Claude Code Adapter

Use this adapter when the setup request is made from Claude Code.

```bash
./install.sh --target claude-code
```

This installs `hermes-grok-tools` through the Claude Code plugin marketplace
flow. It removes an old direct `claude mcp add hermes-grok` registration if one
exists, and it does not modify Codex, Cursor, or Antigravity settings.

When using the generation tools, ask for missing output/cost settings before
calling MCP tools. Use structured AskUserQuestion UI when available. Ask for
quality and aspect ratio for images; quality, duration seconds, and aspect ratio
for video generation; quality for video edit; quality and extension seconds for
video extend. Do not ask non-technical users to choose raw model IDs. Pass
`confirmed_settings: true` after the user supplies, approves, or delegates those
settings.
