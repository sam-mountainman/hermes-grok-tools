# Codex Adapter

Use this adapter when the setup request is made from Codex.

```bash
./install.sh --target codex
```

This installs `grok-cli-tools` through the Codex plugin marketplace. It installs the official Grok CLI when missing, starts `grok login`, and does not modify other AI agent hosts. An old `hermes-grok-tools` installation is removed during migration.

Use `grok_status` for local diagnostics and the other Grok tools only when the user explicitly requests Grok/Grok 4.5 or a Grok second opinion. Grok runs read-only.

Grok 4.5 defaults to `high` reasoning effort. Before `grok_generate_image` or `grok_generate_video`, use `request_user_input` to confirm missing settings. Ask up to three questions: image quality/model, resolution, and aspect ratio; or video model/quality plus resolution, duration, and aspect ratio. Pass `confirmed_settings: true` only after the user supplies, approves, or delegates them. Do not repeat settings already supplied. `grok-imagine-video-1.5` and 1080p require a source image.

Relay successful Grok `answer` values verbatim without summarizing, paraphrasing, translating, reordering, correcting, or truncating them. Preserve formatting and return only Grok's answer by default. Put unavoidable Codex commentary afterward under `Host agent note`. Preserve media paths and URLs exactly.
