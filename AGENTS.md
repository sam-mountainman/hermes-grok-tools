# Grok CLI Tools Setup

When a user gives this repository URL and asks to set it up, clone it and install the plugin only for the current AI agent host.

macOS / Linux:

```bash
./install.sh
```

Windows native PowerShell:

```powershell
.\install.ps1
```

If auto-detection fails, pass exactly one target:

```bash
./install.sh --target codex
./install.sh --target claude-code
./install.sh --target cursor
./install.sh --target antigravity
./install.sh --target gemini
```

On Windows use the corresponding `-Target` value. Do not require WSL.

The installer uses xAI's official Grok CLI installer and starts `grok login`. Browser or device-code authentication requires user interaction. Do not read, print, or copy the contents of `~/.grok/auth.json`.

Install this as a host-native plugin or extension, not as a bare MCP server unless the user explicitly requests the fallback. Do not install it into other AI agent hosts.

After setup:

- Use `grok_status` for local setup/authentication checks; it does not call a model.
- Use `grok_ask` when the user explicitly asks Grok or Grok 4.5 a normal question or wants a Grok second opinion.
- Use `grok_research` when the user explicitly asks Grok to research current information.
- Use `grok_plan` or `grok_review` when the user explicitly asks Grok to plan or review.
- Use `grok_generate_image` or `grok_generate_video` when the user explicitly asks this plugin to create Grok Imagine media.
- Pass the returned `session_id` to continue the same Grok conversation.
- Do not invoke Grok for every ordinary question without a routing reason; it adds latency and consumes the user's Grok allowance.

Grok 4.5 uses `high` reasoning effort by default. Only `low`, `medium`, and `high` are valid; map deep/max requests to `high`.

Relay the `answer` returned by `grok_ask`, `grok_research`, `grok_plan`, and `grok_review` verbatim. Do not summarize, paraphrase, translate, reorder, correct, or silently truncate it. Preserve Markdown, code blocks, links, language, and line breaks. The user-facing reply should contain only Grok's answer by default. Put unavoidable host commentary after the complete answer under a separate `Host agent note` heading. For media tools, preserve returned file paths and URLs exactly.

When a tool returns `error_type: usage_limit`, show the complete error and its clickable SuperGrok upgrade link without rewriting or removing it. Preserve the original Grok CLI error. Do not retry automatically or silently lower reasoning effort.

Before image or video generation, use the host's structured AskUserQuestion/request_user_input UI to confirm missing settings. For images confirm quality/model, 1K/2K resolution, and aspect ratio. For videos confirm model/quality and resolution, 1-15 second duration, and aspect ratio. Do not repeat settings already supplied; if the user delegates them, choose sensible defaults. Pass `confirmed_settings: true` only after the user supplies, approves, or delegates every setting. `grok-imagine-video-1.5` and 1080p require a source image.

The repository inspection path stays read-only. Media tools may create generated output files through Grok Build's bundled Imagine tools. Do not weaken the bridge's `dontAsk`, `Edit(*)`, or `MCPTool(*)` restrictions. `grok_research` is Web research, not a guaranteed dedicated X Search API.
