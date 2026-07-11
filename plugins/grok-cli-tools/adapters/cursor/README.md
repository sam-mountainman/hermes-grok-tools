# Cursor Adapter

Use this adapter when the setup request is made from Cursor.

```bash
./install.sh --target cursor
```

This installs `grok-cli-tools` under `~/.cursor/plugins/local/grok-cli-tools`, installs the official Grok CLI when missing, and starts `grok login`. An old local `hermes-grok-tools` plugin is removed during migration.

For team distribution, import this GitHub repository in Cursor Dashboard > Settings > Plugins > Team Marketplaces.

Use `grok_status` for local diagnostics and the other Grok tools only when the user explicitly requests Grok/Grok 4.5 or a Grok second opinion. Grok runs read-only.

Grok 4.5 defaults to `high` reasoning effort. Before `grok_generate_image` or `grok_generate_video`, use Cursor's structured question UI to confirm missing settings. Ask up to three questions: image quality/model, resolution, and aspect ratio; or video quality plus 480p/720p resolution, 6/10-second duration, and aspect ratio. Pass `confirmed_settings: true` only after the user supplies, approves, or delegates them. Do not repeat settings already supplied. The CLI creates a source image before animation when needed.

Relay successful Grok `answer` values verbatim without summarizing, paraphrasing, translating, reordering, correcting, or truncating them. Preserve formatting and return only Grok's answer by default. Put unavoidable Cursor commentary afterward under `Host agent note`. Preserve media paths and URLs exactly.

If a user changed from the free plan to a paid plan after the current CLI login and still receives a usage limit, run `grok logout` followed by `grok login` before recommending another purchase. Retry once after browser authentication completes. Do not log out for an ambiguous 429 alone.
