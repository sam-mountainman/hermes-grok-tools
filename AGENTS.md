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
- Pass the returned `session_id` to continue the same Grok conversation.
- Do not invoke Grok for every ordinary question without a routing reason; it adds latency and consumes the user's Grok allowance.

The bridge is read-only. Do not weaken its `dontAsk`, `Edit(*)`, or `MCPTool(*)` restrictions. `grok_research` is Web research, not a guaranteed dedicated X Search API. Image and video generation are not exposed because Grok CLI does not currently publish dedicated machine-callable commands for them.
