# Hermes Grok Tools

Use the `hermes-grok` MCP server when the user asks for Hermes Agent Grok OAuth X search, Grok image generation, or Grok video generation.

Before generation-heavy work, call `hermes_grok_status` to confirm Hermes, provider configuration, and xAI OAuth credentials are available.

When the user gives this repository URL and asks Gemini or Antigravity-compatible hosts to set it up, clone the repo and run:

```bash
./install.sh
```

If auto-detection fails, run:

```bash
./install.sh --target gemini
```

OAuth is user-scoped through Hermes. The plugin never stores or ships user credentials.
