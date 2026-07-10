---
name: consult-grok
description: Consult Grok 4.5 through the local Grok CLI for normal questions, second opinions, current-information research, implementation planning, and code review. Use when the user explicitly says Grok, Grok 4.5, asks Grok to answer or research something, or requests a Grok second opinion. Do not invoke implicitly for every ordinary question.
---

Use the `grok-cli` MCP tools:

- Call `grok_status` for setup or authentication checks. It is local-only and spends no model usage.
- Call `grok_ask` for normal questions and second opinions.
- Call `grok_research` when the user explicitly wants Grok-backed current-information or web research.
- Call `grok_plan` when the user asks Grok to design or plan an implementation.
- Call `grok_review` when the user asks Grok to review code or provide a second review opinion.

Pass the project root as `cwd` for repository-aware requests. Forward `effort` only when the user requests a depth such as quick/medium or max/deep. Return Grok's answer clearly as Grok's output; add host-agent commentary separately.

Use the returned `session_id` for follow-up questions in the same Grok conversation. If authentication fails, tell the user to run `grok login`; never read or expose the contents of Grok's credential files.

Do not claim `grok_research` is the dedicated xAI X Search API. Grok CLI officially exposes web research, while dedicated X Search and Grok Imagine API operations require separate API support.
