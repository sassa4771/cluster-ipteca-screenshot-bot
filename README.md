# cluster-ipteca-screenshot-bot

Cluster検索結果のスクリーンショットを自動取得し、Discord通知とpCloudアップロードを行うGitHub Actionsボットです。

## 機能

- **スクリーンショット取得**: 指定URLのスクリーンショットを自動取得（1920x1080、full_page）
- **Discord通知**: スクリーンショット取得の成否をDiscordに通知（画像添付あり）
- **pCloudアップロード**: 取得したスクリーンショットをpCloudに自動アップロード

## 構成

### スクリプト

- `take_screenshot.py` - スクリーンショット取得専用
- `notify_discord.py` - Discord通知専用
- `upload_pcloud.py` - pCloudアップロード専用

### ワークフロー

#### 本番用（自動実行）

- `Production_Screenshot.yml` - スクリーンショット取得（9:00 / 17:00 JST）
- `Production_Notify_Discord.yml` - Discord通知（9:05 / 17:05 JST）
- `Production_Upload_pCloud.yml` - pCloudアップロード（9:10 / 17:10 JST）

#### テスト用（手動実行のみ）

- `Test_Quick.yml` - 全体テスト（スクリーンショット → 通知 → pCloudアップロード、10秒待機）
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
  },
  "pcloud": {
    "enable_upload": true,
    "remote_dir": "/IPTeCA_Cluster_Screenshots"
  }
}
```

#### 設定項目

- `screenshot.url`: スクリーンショット取得対象のURL
- `screenshot.save_dir`: スクリーンショット保存ディレクトリ
- `notification.enable_notify`: 通知の有効/無効（`true` / `false`）
- `notification.target`: 通知先（`"discord"` または `"teams"`）
- `notification.time_window_sec`: 成功判定の閾値（秒）。この時間以内に作成されたファイルがあれば成功
- `pcloud.enable_upload`: pCloudアップロードの有効/無効（`true` / `false`）
- `pcloud.remote_dir`: pCloud上の保存先ディレクトリ

### 3. GitHub Secrets の設定

GitHubリポジトリの **Settings** → **Secrets and variables** → **Actions** で以下を設定：

#### 必須

- `DISCORD_WEBHOOK_URL`: Discord Webhook URL（通知機能を使用する場合）

#### オプション

- `PCLOUD_UPLOAD_CODE`: pCloud Upload link の code（pCloudアップロードを使用する場合）
- `TEAMS_WORKFLOW_URL`: Teams Workflow URL（Teams通知を使用する場合、未実装）

## 使用方法

### 自動実行

各ワークフローは以下のスケジュールで自動実行されます：

- **スクリーンショット取得**: 毎日 JST 9:00 / 17:00
- **Discord通知**: 毎日 JST 9:05 / 17:05
- **pCloudアップロード**: 毎日 JST 9:10 / 17:10

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

#### pCloudアップロード

```bash
pip install requests
export PCLOUD_UPLOAD_CODE="your_upload_code"
python upload_pcloud.py
```

## 動作の流れ

1. **スクリーンショット取得** (`screenshot.yml`)
   - Playwrightで指定URLにアクセス
   - Cookieバナーを閉じる
   - ページ下部までスクロール
   - 1920x1080のviewportでfull_pageスクリーンショットを取得
   - `screenshots/IPTeCA_YYYYMMDD_HHMMSS_UTC.png` に保存

2. **Discord通知** (`notify_discord.yml`)
   - 最新のスクリーンショットファイルを検索
   - 更新時刻をチェック（`time_window_sec`以内なら成功）
   - 結果をDiscordに通知（画像添付あり）

3. **pCloudアップロード** (`upload_pcloud.yml`)
   - 最新のスクリーンショットファイルを検索
   - pCloudにアップロード

## ファイル構成

```
cluster-ipteca-screenshot-bot/
├── take_screenshot.py          # スクリーンショット取得スクリプト
├── notify_discord.py           # Discord通知スクリプト
├── upload_pcloud.py            # pCloudアップロードスクリプト
├── config.json                 # 設定ファイル
├── screenshots/                # スクリーンショット保存ディレクトリ
└── .github/
    └── workflows/
        ├── Production_Screenshot.yml      # スクリーンショット取得（本番）
        ├── Production_Notify_Discord.yml  # Discord通知（本番）
        ├── Production_Upload_pCloud.yml   # pCloudアップロード（本番）
        ├── Test_Quick.yml                 # 全体テスト（テスト用）
        └── Test_Screenshot_Only.yml       # スクリーンショットのみテスト（テスト用）
```

## 依存関係

- **take_screenshot.py**: `playwright`
- **notify_discord.py**: `requests`
- **upload_pcloud.py**: `requests`

## トラブルシューティング

### Discord通知が送信されない

- `DISCORD_WEBHOOK_URL` がGitHub Secretsに設定されているか確認
- `config.json` の `notification.enable_notify` が `true` か確認
- ワークフローの実行ログでエラーメッセージを確認

### pCloudアップロードが失敗する

- `PCLOUD_UPLOAD_CODE` がGitHub Secretsに設定されているか確認
- `config.json` の `pcloud.enable_upload` が `true` か確認
- Upload linkのcodeが有効か確認

### スクリーンショットが取得できない

- 対象URLがアクセス可能か確認
- Playwrightのインストールが正常か確認
- ワークフローの実行ログでエラーメッセージを確認

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。
