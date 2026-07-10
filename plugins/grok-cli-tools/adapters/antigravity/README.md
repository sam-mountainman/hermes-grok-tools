# Antigravity Adapter

Use this adapter when the setup request is made from Antigravity.

```bash
./install.sh --target antigravity
```

This installs a host-native plugin or Gemini-compatible extension, installs the official Grok CLI when missing, and starts `grok login`. It does not modify other AI agent hosts. An old `hermes-grok-tools` plugin is removed during migration.

Use `grok_status` for local diagnostics and the other Grok tools only when the user explicitly requests Grok/Grok 4.5 or a Grok second opinion. Grok runs read-only.

Grok 4.5 defaults to `high` reasoning effort. Before `grok_generate_image` or `grok_generate_video`, use the host's structured question UI to confirm missing settings. Ask up to three questions: image quality/model, resolution, and aspect ratio; or video model/quality plus resolution, duration, and aspect ratio. Pass `confirmed_settings: true` only after the user supplies, approves, or delegates them. Do not repeat settings already supplied. `grok-imagine-video-1.5` and 1080p require a source image.
