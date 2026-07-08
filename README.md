# Hermes Grok Tools

Hermes Agent の Grok OAuth 系ツールを、Codex / Claude Code / Cursor / Antigravity / Gemini から plugin として配布するための marketplace repo です。

目的は「セットアップした AI エージェントだけ」に、そのエージェントの plugin / extension として入れることです。MCP 直登録は過去互換の補助に留め、通常の installer では使いません。

## AI エージェントに頼むだけのセットアップ

ユーザーはこの GitHub URL を AI エージェントに貼って、`セットアップして` と依頼してください。

```text
https://github.com/sam-mountainman/hermes-grok-tools
```

エージェント側は repo を clone して、repo 直下でこれを実行します。

```bash
./install.sh
```

`install.sh` は Codex / Claude Code / Cursor / Antigravity / Gemini を自動判定します。判定できない環境では、エージェントが明示 target を指定します。

```bash
./install.sh --target codex
./install.sh --target claude-code
./install.sh --target cursor
./install.sh --target antigravity
./install.sh --target gemini
```

## 各ホストの入れ方

### Codex

```bash
codex plugin marketplace add https://github.com/sam-mountainman/hermes-grok-tools
codex plugin add hermes-grok-tools@hermes-grok-tools
```

`./install.sh --target codex` もこの flow を使います。`codex mcp add` ではありません。

### Claude Code

```bash
claude plugin marketplace add https://github.com/sam-mountainman/hermes-grok-tools
claude plugin install hermes-grok-tools@hermes-grok-tools --scope user
```

`./install.sh --target claude-code` も `claude plugin marketplace add` + `claude plugin install` を使います。古い `claude mcp add hermes-grok` があれば削除します。

### Cursor

Cursor 用には `.cursor-plugin/marketplace.json` と `plugins/hermes-grok-tools/.cursor-plugin/plugin.json`、plugin root の `mcp.json` を同梱しています。

Cursor には plugin / Marketplace があります。Cursor の公式 plugin repo は root `.cursor-plugin/marketplace.json` と各 plugin の `.cursor-plugin/plugin.json` / `mcp.json` を使う構造です。この repo もその形に合わせています。

Cursor 3.10.17 の CLI には plugin marketplace を追加・install するコマンドが無く、`cursor --add-mcp` は MCP 直登録です。そのため `./install.sh --target cursor` は direct MCP 登録ではなく、`~/.cursor/plugins/local/hermes-grok-tools` に local Cursor plugin としてコピーします。

Team / Enterprise 配布では Cursor Dashboard > Settings > Plugins > Team Marketplaces からこの GitHub repo を import してください。Cursor の Team Marketplaces は GitHub repository URL を読み取り、`.cursor-plugin/marketplace.json` を parse します。

Cursor IDE の plugin UI から個人 install する場合は、Cursor の `/add-plugin` にこの GitHub URL を渡してください。

### Antigravity / Gemini

Gemini CLI / Antigravity 互換 extension として repo root に `gemini-extension.json` を置いています。

```bash
gemini extensions install https://github.com/sam-mountainman/hermes-grok-tools --consent
```

`./install.sh --target gemini` は上記を実行します。`./install.sh --target antigravity` は `agy` があれば Antigravity CLI plugin cache へ plugin として stage し、なければ Gemini extension として install します。

## できること

- `hermes_x_search`: xAI Responses API の `x_search` 経由で X を検索
- `hermes_grok_image`: Hermes `image_generate` を xAI Grok Imagine provider で実行
- `hermes_grok_video`: Hermes `video_generate` を xAI Grok Imagine provider で実行
- `hermes_grok_video_edit`: 既存の公開 MP4 URL を xAI Imagine で編集
- `hermes_grok_video_extend`: 既存の公開 MP4 URL を xAI Imagine で延長
- `hermes_grok_status`: Hermes / OAuth / provider 設定の見える化

## 認証条件

Grok OAuth は初回だけ人間のブラウザ/device login が必要です。

```bash
hermes auth add xai-oauth
```

この repo は認証情報を保存しません。Hermes の `~/.hermes` 側の認証ストアを使います。

## 配布ファイル

| Host | 配布 manifest |
|---|---|
| Codex | `.agents/plugins/marketplace.json` + `plugins/hermes-grok-tools/.codex-plugin/plugin.json` |
| Claude Code | `.claude-plugin/marketplace.json` + `plugins/hermes-grok-tools/.claude-plugin/plugin.json` |
| Cursor | `.cursor-plugin/marketplace.json` + `plugins/hermes-grok-tools/.cursor-plugin/plugin.json` + `plugins/hermes-grok-tools/mcp.json` |
| Antigravity | `.antigravity-plugin/plugin.json` + `mcp_config.json` |
| Gemini | `gemini-extension.json` + `GEMINI.md` |

## 注意点

- X検索は無料 X アカウントのブラウザ検索ではありません。Hermes の `x_search` は xAI API 側の tool です。
- OAuth ログインだけは完全自動化できません。
- 動画の edit/extend は公開 HTTPS MP4 URL が必要です。
- Cursor CLI は 2026-07-08 時点で plugin install コマンドを公開していません。Cursor plugin 自体は存在しますが、CLI ではなく IDE `/add-plugin`、Team Marketplace import、または local plugin install が導線です。

## 開発用確認

```bash
bash -n install.sh
python3 -m pytest -q
python3 /Users/higataiyu/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/hermes-grok-tools
claude plugin validate plugins/hermes-grok-tools
claude plugin validate .
gemini extensions validate .
```
