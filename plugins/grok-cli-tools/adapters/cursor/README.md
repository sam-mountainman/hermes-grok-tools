# Cursor Adapter

Use this adapter when the setup request is made from Cursor.

```bash
./install.sh --target cursor
```

This installs `grok-cli-tools` under `~/.cursor/plugins/local/grok-cli-tools`, installs the official Grok CLI when missing, and starts `grok login`. An old local `hermes-grok-tools` plugin is removed during migration.

For team distribution, import this GitHub repository in Cursor Dashboard > Settings > Plugins > Team Marketplaces.

Use `grok_status` for local diagnostics and the other Grok tools only when the user explicitly requests Grok/Grok 4.5 or a Grok second opinion. Grok runs read-only.

Grok 4.5 defaults to `high` reasoning effort. Before `grok_generate_image` or `grok_generate_video`, use Cursor's structured question UI to confirm missing settings. Ask up to three questions: image quality/model, resolution, and aspect ratio; or video model/quality plus resolution, duration, and aspect ratio. Pass `confirmed_settings: true` only after the user supplies, approves, or delegates them. Do not repeat settings already supplied. `grok-imagine-video-1.5` and 1080p require a source image.
