# Grok CLI Tools

Codex / Claude Code / Cursor / Antigravity / Gemini から、公式 Grok CLI を通じて Grok 4.5 に質問・調査・設計・レビューを依頼し、Grok Imagineで画像・動画を生成するためのplugin marketplace repositoryです。

ホストAIが実装や会話を担当し、必要な場面だけGrok 4.5を外部ブレーンとして呼びます。リポジトリに対するファイル編集や外部MCP呼び出しは許可せず、明示されたメディア生成時だけGrok BuildのImagine toolが出力ファイルを作成します。

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
| `grok_generate_image` | Grok Imagineで画像生成・画像編集 |
| `grok_generate_video` | Grok Imagineで6秒または10秒の動画を生成 |

`grok_ask`などは`session_id`を返します。続きの質問で同じ`session_id`を渡すと、同じGrokセッションを再開できます。既定モデルは`grok-4.5`、既定推論レベルは公式既定と同じ`high`です。Grok 4.5で指定できる推論レベルは`low`、`medium`、`high`です。

通常回答・調査・計画・レビューでGrokから返された`answer`は逐語転送します。ホストAIは要約、言い換え、翻訳、並べ替え、修正、省略をせず、Markdown、コードブロック、リンク、言語、改行を維持します。通常はGrokの回答だけを表示し、必要なホスト側補足は回答全文の後に`Host agent note`として分離します。生成された画像・動画のファイルパスやURLも書き換えません。

利用例:

```text
Grok 4.5にこの質問を聞いて。
Grokにもこの設計のセカンドオピニオンを出させて。
Grokで最新情報を調べて、出典も付けて。
Grokにこの変更をレビューさせて。
Grok Imagineで縦長の画像を作って。
Grokで10秒の動画を作って。
```

プラグイン同梱の `consult-grok` skill は、ユーザーが Grok / Grok 4.5 を明示した場合に適切な tool へルーティングします。全ての普通の質問で勝手に呼び出して利用枠を消費する設計にはしていません。

## 利用上限・レート制限

Grok CLIが無料枠、週間利用枠、クレジット、またはHTTP 429のレート制限を返した場合、pluginは通常エラーと区別して次を表示します。

```text
Grokの利用上限またはレート制限に達しました。

最近、無料プランから有料プランへ変更した場合は、そのことをAIエージェントに伝えてください。

AIエージェントが追加購入を案内する前に、次のコマンドを実行してCLI認証を更新します。

grok logout
grok login

コマンドはユーザー自身で実行する必要はありません。表示されたブラウザでOAuth認証だけ完了してください。認証後、AIエージェントが同じ依頼を一度だけ再試行します。

再認証後も同じ制限が出る場合は、現在のAIエージェントアプリを完全終了して再起動してください。Codexでは再起動後に同じタスクを開き、「再試行して」と伝えます。AI自身がホストを終了すると処理を継続できないため、ホストの強制終了・自動再起動は行いません。

利用を続ける方法:

1. [SuperGrokプランを確認・アップグレード](https://grok.com/supergrok?referrer=pricing&target=supergrok)
2. [X PremiumまたはPremium+へ加入](https://x.com/i/premium_sign_up)
   加入後、grok.comのSettings → AccountでXアカウントを連携してください。
3. 利用枠のリセットを待ってから再試行する

Grok CLIの元エラー:
<original error>
```

MCPの`structuredContent`にも`error_type: usage_limit`、後方互換用の`upgrade_plan`と`upgrade_url`、SuperGrokとX Premiumの選択肢を含む`upgrade_options`、再認証条件とコマンドを含む`reauthentication`、再認証後も失敗した場合の`host_restart_fallback`、`original_error`を返します。

ホストAIは、ユーザーが現在のCLIログイン後にプランを変更したと伝えた場合、または有効な有料プランと利用枠の残りを確認できた場合、追加購入を勧める前にホストのターミナルで`grok logout`、`grok login`を順番に実行します。ブラウザ認証完了後だけ元の依頼を一度再試行します。曖昧なHTTP 429だけを根拠に勝手にログアウトはしません。Extra Usage Creditsは案内せず、推論レベルも無断で下げません。

## 画像・動画生成前の確認

画像・動画を生成する前に、ホストAIは`AskUserQuestion`、`request_user_input`などの構造化質問UIで未指定の設定を確認します。既に指定された項目は聞き直しません。「任せる」と言われた場合は推奨値を選びます。

画像で確認する項目:

- 品質・モデル: 高品質`grok-imagine-image-quality`、または標準`grok-imagine-image`
- 解像度: 2K、または1K
- 縦横比: 16:9、9:16、1:1など

動画で確認する項目:

- 品質・解像度: 高品質/HD 720p、または標準480p。動画モデルはGrok CLIが自動選択
- 秒数: 6秒、または10秒
- 縦横比: 16:9、9:16、1:1など

公式Grok CLIの同梱ツールには直接のtext-to-videoがないため、テキストだけの依頼では最初の静止画を作り、`image_to_video`で動かします。CLIが受け付ける秒数は6秒または10秒です。確認後だけtoolへ`confirmed_settings: true`を渡すため、設定未確認のまま生成枠を消費しません。

## 認証

通常は installer 中にブラウザログインが始まります。

```bash
grok login
```

無料プランから有料プランへ変更した後もCLIが以前の制限を返す場合は、CLIのOAuthセッションを更新します。

```bash
grok logout
grok login
```

新規チャットの作成だけではCLIの認証状態は更新されません。

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
- 画像・動画生成はGrok Buildに同梱されたImagine toolをGrok 4.5経由で呼びます。直接Imagine API integrationではなく、OAuthでログインしたGrok CLIの利用条件に従います。
- 生成モデルや解像度の提供状況はxAI側で変更される可能性があります。
- Grok CLI の利用可否、モデル、料金、利用枠は xAI 側のアカウントと提供条件に従います。

## セキュリティ

MCP bridgeはGrok CLIを`dontAsk` modeで実行し、`Edit(*)`と`MCPTool(*)`を拒否します。`--always-approve`は使いません。Grokはrepositoryを読み取り、検索、レビューできますが、ソースファイルを変更しません。画像・動画生成時だけImagine toolが生成物を保存します。

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
