# Cursor Adapter

Use this adapter when the setup request is made from Cursor.

```bash
./install.sh --target cursor
```

Cursor setup is distributed as a Cursor Team Marketplace using the repo root
`.cursor-plugin/marketplace.json`.

Cursor has plugins and a plugin marketplace. Cursor 3.10.17 does not expose a
CLI command for installing a Team Marketplace, and `cursor --add-mcp` is direct
MCP registration rather than plugin installation.

`./install.sh --target cursor` therefore installs this as a local Cursor plugin
under `~/.cursor/plugins/local/hermes-grok-tools`.

For team distribution, import the GitHub repository URL in Cursor Dashboard >
Settings > Plugins > Team Marketplaces.

When using the generation tools, ask for missing output/cost settings before
calling MCP tools. Use Cursor's structured question UI when available, or a
concise text fallback. Ask for quality and aspect ratio for images; quality,
duration seconds, and aspect ratio for video generation; quality for video edit;
quality and extension seconds for video extend. Do not ask non-technical users
to choose raw model IDs. Pass `confirmed_settings: true` after the user supplies,
approves, or delegates those settings.
