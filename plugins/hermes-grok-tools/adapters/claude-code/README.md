# Claude Code Adapter

Use this adapter when the setup request is made from Claude Code.

```bash
./install.sh --target claude-code
```

This installs `hermes-grok-tools` through the Claude Code plugin marketplace
flow. It removes an old direct `claude mcp add hermes-grok` registration if one
exists, and it does not modify Codex, Cursor, or Antigravity settings.
