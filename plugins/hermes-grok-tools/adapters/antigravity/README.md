# Antigravity Adapter

Use this adapter when the setup request is made from Antigravity.

```bash
./install.sh --target antigravity
```

This installs a plugin/extension, not a direct MCP registration. If `agy` is
available, the installer stages the plugin under the Antigravity CLI plugin
cache. Otherwise it installs the repo root `gemini-extension.json` with
`gemini extensions install`.
