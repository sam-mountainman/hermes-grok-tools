# Claude Code Adapter

Use this adapter when the setup request is made from Claude Code.

```bash
./install.sh --target claude-code
```

This installs `grok-cli-tools` through the Claude Code plugin marketplace. It installs the official Grok CLI when missing, starts `grok login`, and does not modify other AI agent hosts. An old `hermes-grok-tools` installation is removed during migration.

Use `grok_status` for local diagnostics and the other Grok tools only when the user explicitly requests Grok/Grok 4.5 or a Grok second opinion. Grok runs read-only.
