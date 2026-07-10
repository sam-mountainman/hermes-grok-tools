# Grok CLI Tools

Use the `grok-cli` MCP server when the user explicitly asks Grok or Grok 4.5 for an answer, research, implementation planning, or code review.

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

Grok runs read-only. `grok_research` uses Grok CLI Web research and is not a guaranteed dedicated X Search API. Image and video generation are not exposed by this plugin.
