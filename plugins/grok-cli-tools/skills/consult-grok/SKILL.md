---
name: consult-grok
description: Consult Grok 4.5 through the local Grok CLI for normal questions, second opinions, current-information research, implementation planning, code review, and Grok Imagine image or video generation. Use when the user explicitly says Grok, Grok 4.5, asks Grok to answer or research something, requests a Grok second opinion, or asks this plugin to generate media. Do not invoke implicitly for every ordinary question.
---

Use the `grok-cli` MCP tools:

- Call `grok_status` for setup or authentication checks. It is local-only and spends no model usage.
- Call `grok_ask` for normal questions and second opinions.
- Call `grok_research` when the user explicitly wants Grok-backed current-information or web research.
- Call `grok_plan` when the user asks Grok to design or plan an implementation.
- Call `grok_review` when the user asks Grok to review code or provide a second review opinion.
- Call `grok_generate_image` for Grok Imagine image generation or editing.
- Call `grok_generate_video` for Grok Imagine text-to-video or image-to-video generation.

Pass the project root as `cwd` for repository-aware requests. The default reasoning effort is `high`. Use `low` only when the user asks for a quick answer and `medium` when they explicitly prefer a speed/quality balance. Grok 4.5 does not accept `xhigh` or `max`; interpret deep/max requests as `high`. Return Grok's answer clearly as Grok's output; add host-agent commentary separately.

## Media confirmation

Before every image or video tool call, resolve output and cost-affecting settings with the user. Use the host's structured `AskUserQuestion`, `request_user_input`, or equivalent UI. Ask only for values not already supplied. If the user already supplied all values, or explicitly says to choose automatically, treat those values as confirmed without asking them again. Always pass `confirmed_settings: true` after the user supplies, approves, or delegates the settings.

For images, confirm up to three items:

- Quality/model: High quality (`grok-imagine-image-quality`, recommended) or Standard (`grok-imagine-image`).
- Resolution: 2K (recommended for final output) or 1K (faster/lower cost).
- Aspect ratio: offer context-appropriate choices, normally 16:9, 9:16, and 1:1.

For videos, confirm up to three items:

- Quality/model and resolution: for text-to-video offer Standard 720p (recommended) or Fast 480p using `grok-imagine-video`; when a source image is present, also offer High quality 1080p using `grok-imagine-video-1.5`.
- Duration: offer 5, 10 (recommended), or 15 seconds unless the user already specified another valid 1-15 second value.
- Aspect ratio: offer context-appropriate choices, normally 16:9, 9:16, and 1:1.

Do not offer `grok-imagine-video-1.5` or 1080p for text-only video generation; both require a source image. Pass source files as absolute local paths. If structured questions are unavailable in the host, ask one concise text question containing the same choices. Never silently spend generation allowance with unconfirmed settings.

Use the returned `session_id` for follow-up questions in the same Grok conversation. If authentication fails, tell the user to run `grok login`; never read or expose the contents of Grok's credential files.

Do not claim `grok_research` is the dedicated xAI X Search API. Grok CLI officially exposes web research. Media tools use Grok Build's bundled Imagine capabilities through the user's Grok CLI OAuth session; do not claim they are direct Imagine API calls.
