# Antigravity Adapter

Use this adapter when the setup request is made from Antigravity.

```bash
./install.sh --target antigravity
```

This installs a host-native plugin or Gemini-compatible extension, installs the official Grok CLI when missing, and starts `grok login`. It does not modify other AI agent hosts. An old `hermes-grok-tools` plugin is removed during migration.

Use `grok_status` for local diagnostics and the other Grok tools only when the user explicitly requests Grok/Grok 4.5 or a Grok second opinion. Grok runs read-only.
