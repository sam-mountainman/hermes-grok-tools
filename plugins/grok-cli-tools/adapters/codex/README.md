# Codex Adapter

Use this adapter when the setup request is made from Codex.

```bash
./install.sh --target codex
```

This installs `grok-cli-tools` through the Codex plugin marketplace. It installs the official Grok CLI when missing, starts `grok login`, and does not modify other AI agent hosts. An old `hermes-grok-tools` installation is removed during migration.

Use `grok_status` for local diagnostics and the other Grok tools only when the user explicitly requests Grok/Grok 4.5 or a Grok second opinion. Grok runs read-only.

Grok 4.5 defaults to `high` reasoning effort. Before `grok_generate_image` or `grok_generate_video`, use `request_user_input` to confirm missing settings. Ask up to three questions: image quality/model, resolution, and aspect ratio; or video quality plus 480p/720p resolution, 6/10-second duration, and aspect ratio. Pass `confirmed_settings: true` only after the user supplies, approves, or delegates them. Do not repeat settings already supplied. The CLI creates a source image before animation when needed.

Relay successful Grok `answer` values verbatim without summarizing, paraphrasing, translating, reordering, correcting, or truncating them. Preserve formatting and return only Grok's answer by default. Put unavoidable Codex commentary afterward under `Host agent note`. Preserve media paths and URLs exactly.

If a user changed from the free plan to a paid plan after the current CLI login and still receives a usage limit, run `grok logout` followed by `grok login` before recommending another purchase. Retry once after browser authentication completes. Do not log out for an ambiguous 429 alone.
