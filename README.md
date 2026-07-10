# Grok CLI Tools

Codex / Claude Code / Cursor / Antigravity / Gemini から、公式 Grok CLI を通じて Grok 4.5 に質問・調査・設計・レビューを依頼するための plugin marketplace repository です。

ホスト AI が実装や会話を担当し、必要な場面だけ Grok 4.5 を外部ブレーンとして呼びます。Grok は読み取り専用で起動し、ファイル編集や外部 MCP 呼び出しを許可しません。

## AI エージェントに頼むだけのセットアップ

使いたい AI エージェントへ次の一文を送ってください。

```text
https://github.com/sam-mountainman/grok-cli-tools をセットアップして。
```

依頼を受けた AI エージェントは repository を clone し、自分自身のホストだけをセットアップします。

macOS / Linux:

```bash
./install.sh
```

Windows native PowerShell:

```powershell
.\install.ps1
```

installer は公式 Grok CLI がなければインストールし、`grok login` を開始します。初回のブラウザまたは device-code 認証だけはユーザー操作が必要です。その後、Codex / Claude Code / Cursor / Antigravity / Gemini のうち、依頼元に対応する plugin / extension だけを登録します。

自動判定できない場合:

```bash
./install.sh --target codex
./install.sh --target claude-code
./install.sh --target cursor
./install.sh --target antigravity
./install.sh --target gemini
```

Windows native:

```powershell
.\install.ps1 -Target codex
.\install.ps1 -Target claude-code
.\install.ps1 -Target cursor
.\install.ps1 -Target antigravity
.\install.ps1 -Target gemini
```

## 提供ツール

| Tool | 用途 |
|---|---|
| `grok_status` | Grok CLI、認証の存在、既定モデルをローカル確認。モデル利用なし |
| `grok_ask` | Grok 4.5 に普通の質問、相談、セカンドオピニオンを依頼 |
| `grok_research` | Grok CLI の Web 検索を使った現在情報の調査と出典収集 |
| `grok_plan` | repository を読み取り専用で調べ、実装計画を作成 |
| `grok_review` | repository と `git diff` を読み取り専用でレビュー |

`grok_ask` などは `session_id` を返します。続きの質問で同じ `session_id` を渡すと、同じ Grok セッションを再開できます。既定モデルは `grok-4.5` で、必要な場合だけ `model` を上書きできます。

利用例:

```text
Grok 4.5にこの質問を聞いて。
Grokにもこの設計のセカンドオピニオンを出させて。
Grokで最新情報を調べて、出典も付けて。
Grokにこの変更をレビューさせて。
```

プラグイン同梱の `consult-grok` skill は、ユーザーが Grok / Grok 4.5 を明示した場合に適切な tool へルーティングします。全ての普通の質問で勝手に呼び出して利用枠を消費する設計にはしていません。

## 認証

通常は installer 中にブラウザログインが始まります。

```bash
grok login
```

ブラウザを使えない環境:

```bash
grok login --device-auth
```

CI や従量課金の API key を使う環境では `XAI_API_KEY` も利用できます。plugin は token や `~/.grok/auth.json` の内容を読み取らず、公式 Grok CLI に認証を任せます。

## 各ホストへの登録

### Codex

```bash
codex plugin marketplace add https://github.com/sam-mountainman/grok-cli-tools
codex plugin add grok-cli-tools@grok-cli-tools
```

### Claude Code

```bash
claude plugin marketplace add https://github.com/sam-mountainman/grok-cli-tools
claude plugin install grok-cli-tools@grok-cli-tools --scope user
```

### Cursor

Cursor 用の `.cursor-plugin/marketplace.json` と plugin manifest を同梱しています。個人利用では Cursor の `/add-plugin` に GitHub URL を渡すか、installer が `~/.cursor/plugins/local/grok-cli-tools` へ配置します。Team / Enterprise は Cursor Dashboard の Team Marketplaces へ repository URL を追加します。

### Antigravity / Gemini

`gemini-extension.json` と Antigravity plugin manifest を同梱しています。

```bash
gemini extensions install https://github.com/sam-mountainman/grok-cli-tools --consent
```

## Windows native

WSL は不要です。PowerShell installer は次を行います。

- xAI 公式 `https://x.ai/cli/install.ps1` で native Windows Grok CLI を導入
- `grok login` でブラウザ認証を開始
- Python 3 がなければ `winget` で導入
- `%LOCALAPPDATA%\grok-cli-tools\bin\python3.cmd` を作成
- 依頼元 AI エージェントの plugin / extension だけを登録

インストール後は対象の AI エージェントを一度再起動し、`Grokの状態を確認して` と依頼してください。

## 制約

- `grok_research` は Grok CLI の Web 検索です。xAI Responses API の専用 `x_search` tool を保証するものではありません。
- 公式 Grok CLI は、画像・動画生成を機械的に呼ぶ専用 CLI command を現在公開していません。そのため旧 Hermes 版の画像・動画生成 tool は含めていません。
- 専用 X Search や Grok Imagine API を追加する場合は、別途 `XAI_API_KEY` を使う直接 API integration が必要です。
- Grok CLI の利用可否、モデル、料金、利用枠は xAI 側のアカウントと提供条件に従います。

## セキュリティ

MCP bridge は Grok CLI を `dontAsk` mode で実行し、`Edit(*)` と `MCPTool(*)` を拒否します。`--always-approve` は使いません。Grok は repository を読み取り、検索、レビューできますが、ファイルを変更しません。

## 商標

plugin icon は X 公式 Brand Toolkit の X logo asset を使用しています。X、Grok、関連する名称とロゴは各権利者の商標です。この project は X Corp. または xAI の公式・提携 plugin ではありません。asset の利用には X の Brand Guidelines が適用されます。詳細は `THIRD_PARTY_NOTICES.md` を参照してください。

## 開発用確認

```bash
bash -n install.sh
python3 -m pytest -q
python3 /Users/higataiyu/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/grok-cli-tools
python3 /Users/higataiyu/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugins/grok-cli-tools/skills/consult-grok
claude plugin validate plugins/grok-cli-tools
claude plugin validate .
gemini extensions validate .
```
