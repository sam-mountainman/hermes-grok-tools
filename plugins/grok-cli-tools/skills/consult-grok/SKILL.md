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
- Call `grok_generate_video` for a Grok Imagine video from text or a supplied first-shot image. Grok CLI stages source images and animates them with `image_to_video`.

Pass the project root as `cwd` for repository-aware requests. The default reasoning effort is `high`. Use `low` only when the user asks for a quick answer and `medium` when they explicitly prefer a speed/quality balance. Grok 4.5 does not accept `xhigh` or `max`; interpret deep/max requests as `high`.

## Verbatim relay

For `grok_ask`, `grok_research`, `grok_plan`, and `grok_review`, return the MCP result's `answer` text verbatim as Grok's response. Do not summarize, paraphrase, rewrite, translate, reorder, correct, or silently truncate it. Preserve its language, wording, Markdown, headings, lists, code fences, links, and line breaks. Do not merge the host agent's own prose into Grok's text.

By default, the user-facing reply should contain only Grok's exact `answer`. If host-agent commentary is necessary, place it after the complete Grok answer under a clearly separate `Host agent note` heading. Never put commentary before, inside, or in place of Grok's answer. If a host output limit prevents full relay, say that explicitly instead of pretending a shortened response is verbatim.

For media tools, relay the returned generated file path or URL exactly. The host may render or link the media after presenting that exact value, but must not replace it with an invented path or rewritten URL.

## Media confirmation

Before every image or video tool call, resolve output and cost-affecting settings with the user. Use the host's structured `AskUserQuestion`, `request_user_input`, or equivalent UI. Ask only for values not already supplied. If the user already supplied all values, or explicitly says to choose automatically, treat those values as confirmed without asking them again. Always pass `confirmed_settings: true` after the user supplies, approves, or delegates the settings.

For images, confirm up to three items:

- Quality/model: High quality (`grok-imagine-image-quality`, recommended) or Standard (`grok-imagine-image`).
- Resolution: 2K (recommended for final output) or 1K (faster/lower cost).
- Aspect ratio: offer context-appropriate choices, normally 16:9, 9:16, and 1:1.

For videos, confirm up to three items:

- Quality and resolution: High/HD 720p (recommended) or Standard 480p. Grok CLI selects the underlying Imagine video model automatically.
- Duration: 6 seconds or 10 seconds (recommended).
- Aspect ratio: offer context-appropriate choices, normally 16:9, 9:16, and 1:1.

The bundled CLI has no direct text-to-video tool. When the user supplies only text, it creates a source image and animates it with `image_to_video`. Pass a supplied source image as an absolute local path. If structured questions are unavailable in the host, ask one concise text question containing the same choices. Never silently spend generation allowance with unconfirmed settings.

Use the returned `session_id` for follow-up questions in the same Grok conversation. If authentication fails, tell the user to run `grok login`; never read or expose the contents of Grok's credential files.

If a tool returns `error_type: usage_limit`, show its complete error message without removing or rewriting any recovery option. The user-facing response must include both clickable links for SuperGrok and X Premium/Premium+, plus the original Grok CLI error. Do not mention Extra Usage Credits. Do not retry automatically or silently reduce reasoning quality.

Do not claim `grok_research` is the dedicated xAI X Search API. Grok CLI officially exposes web research. Media tools use Grok Build's bundled Imagine capabilities through the user's Grok CLI OAuth session; do not claim they are direct Imagine API calls.
