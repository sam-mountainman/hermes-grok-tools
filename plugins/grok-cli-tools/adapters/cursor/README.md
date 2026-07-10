# Cursor Adapter

Use this adapter when the setup request is made from Cursor.

```bash
./install.sh --target cursor
```

This installs `grok-cli-tools` under `~/.cursor/plugins/local/grok-cli-tools`, installs the official Grok CLI when missing, and starts `grok login`. An old local `hermes-grok-tools` plugin is removed during migration.

For team distribution, import this GitHub repository in Cursor Dashboard > Settings > Plugins > Team Marketplaces.

Use `grok_status` for local diagnostics and the other Grok tools only when the user explicitly requests Grok/Grok 4.5 or a Grok second opinion. Grok runs read-only.
