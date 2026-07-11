# Grok CLI Tools

Use the `grok-cli` MCP server when the user explicitly asks Grok or Grok 4.5 for an answer, research, implementation planning, code review, or Grok Imagine media generation.

Call `grok_status` for local setup/authentication checks. It does not call a model. Use the returned `session_id` for follow-up questions in the same Grok conversation. Do not invoke Grok for every ordinary question without a routing reason.

When the user asks Gemini or Antigravity to set up this repository, clone it and run:

```bash
./install.sh --target gemini
```

Windows native PowerShell:

```powershell
.\install.ps1 -Target gemini
```

For Antigravity, use the `antigravity` target. The installer installs the official Grok CLI if needed, starts `grok login`, and installs only the requested extension/plugin.

Grok 4.5 defaults to `high` reasoning effort. Before calling `grok_generate_image` or `grok_generate_video`, use the host's structured question UI to confirm missing settings. Confirm image quality/model, resolution, and aspect ratio; confirm video quality, 480p/720p resolution, 6/10-second duration, and aspect ratio. Pass `confirmed_settings: true` only after the user supplies, approves, or delegates them. Do not repeat settings already supplied. Grok CLI creates a source image before animation when needed.

Relay every successful Grok `answer` verbatim. Do not summarize, paraphrase, translate, reorder, correct, or silently truncate it. Preserve Markdown, code blocks, links, language, and line breaks. Reply with only Grok's answer by default. Put unavoidable Gemini or Antigravity commentary after the complete answer under a separate `Host agent note` heading. Preserve generated media paths and URLs exactly.

When a tool returns `error_type: usage_limit`, show the complete error and both clickable recovery links for SuperGrok and X Premium/Premium+ without rewriting or removing them. Do not mention Extra Usage Credits. Preserve the original Grok CLI error. Do not retry automatically or silently lower reasoning effort.

If the user upgraded or changed plans after the current CLI login, or shows an active paid plan with remaining usage, run `grok logout` and then `grok login` in the host terminal before recommending another purchase. Tell the user to complete browser or device-code authentication, then retry the original Grok request once. Do not log out solely because of an ambiguous 429.

Repository inspection stays read-only; only generated media files may be created through Grok Build's bundled Imagine tools. `grok_research` is not a guaranteed dedicated X Search API.
