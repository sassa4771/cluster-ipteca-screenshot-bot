# cluster-ipteca-screenshot-bot

Cluster検索結果のスクリーンショットを自動取得し、Discord通知を行うGitHub Actionsボットです。

## 機能

- **スクリーンショット取得**: 指定URLのスクリーンショットを自動取得（1920x1080、full_page）
- **Discord通知**: スクリーンショット取得の成否をDiscordに通知（画像添付あり）
- **Gitリポジトリ保存**: 取得したスクリーンショットをリポジトリの`screenshots/`に自動コミット・プッシュ
- **グラフ作成**: スクリーンショット取得履歴を解析してグラフを作成（`graphs/`フォルダに保存）

## 構成

### スクリプト

- `take_screenshot.py` - スクリーンショット取得専用
- `notify_discord.py` - Discord通知専用
- `analyze_screenshots.py` - スクリーンショット解析・グラフ作成専用

### ワークフロー

#### 本番用（自動実行）

- `Production_Screenshot_Notify.yml` - スクリーンショット取得・通知（6:00 / 13:00 / 18:00 / 24:00 JST）
  - スクリーンショット取得 → Gitにコミット・プッシュ → Discord通知
- `Production_Analyze_Screenshots.yml` - スクリーンショット解析・グラフ作成（24:00 JST、毎日1回）
  - スクリーンショット履歴を解析してグラフを作成 → Gitにコミット・プッシュ

#### テスト用（手動実行のみ）

- `Test_Quick.yml` - 全体テスト（スクリーンショット → 通知、10秒待機）
- `Test_Screenshot_Only.yml` - スクリーンショット取得のみテスト

各ワークフローは独立しており、`workflow_dispatch`で手動実行も可能です。

## セットアップ

### 1. リポジトリのクローン

```bash
git clone https://github.com/sassa4771/cluster-ipteca-screenshot-bot.git
cd cluster-ipteca-screenshot-bot
```

### 2. config.json の設定

`config.json` を編集して設定を変更できます：

```json
{
  "screenshot": {
    "url": "https://cluster.mu/search?q=IPTeCA&type=world",
    "save_dir": "screenshots"
  },
  "notification": {
    "enable_notify": true,
    "target": "discord",
    "time_window_sec": 600
  }
}
```

#### 設定項目

- `screenshot.url`: スクリーンショット取得対象のURL
- `screenshot.save_dir`: スクリーンショット保存ディレクトリ
- `notification.enable_notify`: 通知の有効/無効（`true` / `false`）
- `notification.target`: 通知先（`"discord"` または `"teams"`）
- `notification.time_window_sec`: 成功判定の閾値（秒）。この時間以内に作成されたファイルがあれば成功

### 3. GitHub Secrets の設定

GitHubリポジトリの **Settings** → **Secrets and variables** → **Actions** で以下を設定：

#### 必須

- `DISCORD_WEBHOOK_URL`: Discord Webhook URL（通知機能を使用する場合）

## 使用方法

### 自動実行

本番用ワークフローは以下のスケジュールで自動実行されます：

- **Production_Screenshot_Notify**: 毎日 JST 6:00 / 13:00 / 18:00 / 24:00
  - スクリーンショット取得 → Gitにコミット・プッシュ → Discord通知
- **Production_Analyze_Screenshots**: 毎日 JST 24:00（1日1回）
  - スクリーンショット履歴を解析してグラフを作成 → Gitにコミット・プッシュ

### 手動実行

1. GitHubリポジトリの **Actions** タブを開く
2. 実行したいワークフローを選択
3. **Run workflow** をクリック
4. ブランチを選択して実行

### ローカル実行

#### スクリーンショット取得

```bash
pip install playwright requests
python -m playwright install --with-deps chromium
python take_screenshot.py
```

#### Discord通知

```bash
pip install requests
export DISCORD_WEBHOOK_URL="your_webhook_url"
python notify_discord.py
```


## 動作の流れ

1. **スクリーンショット取得**
   - Playwrightで指定URLにアクセス
   - Cookieバナーを閉じる
   - ページ下部までスクロール
   - 1920x1080のviewportでfull_pageスクリーンショットを取得
   - `screenshots/IPTeCA_YYYYMMDD_HHMMSS_JST.png` に保存

2. **Gitにコミット・プッシュ**
   - スクリーンショットをリポジトリの`screenshots/`にコミット（コミットメッセージはJST時刻）
   - 自動的にプッシュしてGitHub上で確認可能に

3. **Discord通知**
   - 最新のスクリーンショットファイルを検索
   - 更新時刻をチェック（`time_window_sec`以内なら成功）
   - 結果をDiscordに通知（画像添付あり）

## ファイル構成

```
cluster-ipteca-screenshot-bot/
├── take_screenshot.py          # スクリーンショット取得スクリプト
├── notify_discord.py           # Discord通知スクリプト
├── analyze_screenshots.py      # スクリーンショット解析・グラフ作成スクリプト
├── config.json                 # 設定ファイル
├── screenshots/                # スクリーンショット保存ディレクトリ（Gitにコミットされる）
├── graphs/                     # グラフ保存ディレクトリ
└── .github/
    └── workflows/
        ├── Production_Screenshot_Notify.yml    # スクリーンショット取得・通知（本番）
        └── Production_Analyze_Screenshots.yml  # スクリーンショット解析・グラフ作成（本番）
```

## 依存関係

- **take_screenshot.py**: `playwright`
- **notify_discord.py**: `requests`
- **analyze_screenshots.py**: `pandas`, `matplotlib`

## トラブルシューティング

### Discord通知が送信されない

- `DISCORD_WEBHOOK_URL` がGitHub Secretsに設定されているか確認
- `config.json` の `notification.enable_notify` が `true` か確認
- ワークフローの実行ログでエラーメッセージを確認

### スクリーンショットが取得できない

- 対象URLがアクセス可能か確認
- Playwrightのインストールが正常か確認
- ワークフローの実行ログでエラーメッセージを確認

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。
