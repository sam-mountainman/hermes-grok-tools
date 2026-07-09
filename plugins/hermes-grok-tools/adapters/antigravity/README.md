# Antigravity Adapter

Use this adapter when the setup request is made from Antigravity.

```bash
./install.sh --target antigravity
```

This installs a plugin/extension, not a direct MCP registration. If `agy` is
available, the installer stages the plugin under the Antigravity CLI plugin
cache. Otherwise it installs the repo root `gemini-extension.json` with
`gemini extensions install`.

When using the generation tools, ask for missing output/cost settings before
calling MCP tools. Use structured question UI when available, or a concise text
fallback. Ask for quality and aspect ratio for images; quality, duration seconds,
and aspect ratio for video generation; quality for video edit; quality and
extension seconds for video extend. Do not ask non-technical users to choose raw
model IDs. Pass `confirmed_settings: true` after the user supplies, approves, or
delegates those settings.
