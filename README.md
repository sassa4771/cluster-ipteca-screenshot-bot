# cluster-ipteca-screenshot-bot

Cluster検索結果のスクリーンショットを自動取得し、Discord通知を行うGitHub Actionsボットです。

## 機能

- **スクリーンショット取得**: 指定URLのスクリーンショットを自動取得（1920x1080、full_page）
- **HTML取得**: Cluster検索結果のHTMLを自動取得し、各ゾーンの訪問者数といいね数を抽出
- **Discord通知**: スクリーンショット取得の成否をDiscordに通知（画像添付あり）
- **Gitリポジトリ保存**: 取得したスクリーンショットとHTMLをリポジトリに自動コミット・プッシュ
- **グラフ作成**: HTML取得履歴を解析してグラフを作成（`graphs/`フォルダに保存）
  - 各ゾーンの訪問者数といいね数の時系列グラフ
  - HTML取得のタイムライン、日別取得数、時間帯別分布
  - イベント情報の重畳表示機能
- **手動データ対応**: スクリーンショットから手動で入力したデータもグラフに反映可能

## 構成

### スクリプト

- `take_screenshot.py` - スクリーンショット取得専用
- `fetch_html.py` - HTML取得専用（各ゾーンの訪問者数といいね数を抽出）
- `notify_discord.py` - Discord通知専用
- `notify_graphs_discord.py` - グラフをDiscordに送信
- `analyze_html.py` - HTML解析・グラフ作成専用（HTMLファイルからデータを取得、イベント情報を重畳表示）

### ワークフロー

#### 本番用（自動実行）

- `Production_Screenshot_Notify.yml` - スクリーンショット・HTML取得・通知（6:00 / 13:00 / 18:00 / 24:00 JST）
  - スクリーンショット取得 → HTML取得 → Gitにコミット・プッシュ → Discord通知
- `Production_Analyze_HTML.yml` - HTML解析・グラフ作成（24:00 JST、毎日1回）
  - HTMLファイル履歴を解析してグラフを作成 → イベント情報を重畳表示 → Gitにコミット・プッシュ

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
  - スクリーンショット取得 → HTML取得 → Gitにコミット・プッシュ → Discord通知
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

#### HTML取得

```bash
pip install playwright requests beautifulsoup4
python -m playwright install --with-deps chromium
python fetch_html.py
```

#### グラフ作成・分析

```bash
pip install pandas matplotlib beautifulsoup4
python analyze_html.py
```

#### Discord通知

```bash
pip install requests
export DISCORD_WEBHOOK_URL="your_webhook_url"
python notify_discord.py
```

#### グラフをDiscordに送信

```bash
pip install requests
export DISCORD_WEBHOOK_URL="your_webhook_url"
python notify_graphs_discord.py
```


## 動作の流れ

### スクリーンショット・HTML取得の流れ

1. **スクリーンショット取得**
   - Playwrightで指定URLにアクセス
   - Cookieバナーを閉じる
   - ページ下部までスクロール
   - 1920x1080のviewportでfull_pageスクリーンショットを取得
   - `screenshots/IPTeCA_YYYYMMDD_HHMMSS_JST.png` に保存

2. **HTML取得**
   - 同じURLからHTMLを取得
   - BeautifulSoupで各ゾーンの訪問者数といいね数を抽出
   - `html/IPTeCA_YYYYMMDD_HHMMSS_JST.html` に保存

3. **Gitにコミット・プッシュ**
   - スクリーンショットとHTMLをリポジトリにコミット（コミットメッセージはJST時刻）
   - 自動的にプッシュしてGitHub上で確認可能に

4. **Discord通知**
   - 最新のスクリーンショットファイルを検索
   - 更新時刻をチェック（`time_window_sec`以内なら成功）
   - 結果をDiscordに通知（画像添付あり）

### グラフ作成の流れ

1. **データ収集**
   - `html/`フォルダ内のHTMLファイルから各ゾーンのデータを抽出
   - `graphs/html_data.csv`にデータを保存（手動データも含む）

2. **イベント情報の読み込み**
   - `events.json`からイベント情報を読み込み
   - グラフに重畳表示する準備

3. **グラフ作成**
   - 各ゾーンの訪問者数といいね数の時系列グラフ
   - HTML取得のタイムライン、日別取得数、時間帯別分布
   - イベント情報を垂直線とテキストで重畳表示

4. **保存・通知**
   - `graphs/`フォルダにグラフを保存
   - 必要に応じてDiscordに送信

## グラフ出力について

`analyze_html.py`を実行すると、以下のグラフが`graphs/`フォルダに生成されます：

### 主要なグラフ

#### `zone_visitors_timeline.png` - 各ゾーン来場者数の推移

各ゾーンの訪問者数の時系列グラフです。最新のデータ点には「人数＋取得日時（JST）」をラベル表示し、タイトルに全ゾーンの最新合計人数を表示します：

- **6つのゾーンの訪問者数推移**
  - エントランス
  - メインロビー
  - 研究成果・技術内容
  - CSAP
  - 地域貢献・展開
  - ものづくり教育

- **最新時刻の数値と日時を一目で確認**
  - 各ゾーンの最新データ点の横に「人数（人）＋取得日時(JST)」を表示
- **合計人数をタイトルで表示**
  - 全ゾーンの最新データの合計人数をタイトルに記載

- **手動データの反映**
  - HTMLが取得できない期間の手動データも表示
  - CSVファイル（`graphs/html_data.csv`）に手動で入力したデータも反映

#### `zone_likes_timeline.png` - 各ゾーンいいね数の推移

各ゾーンのいいね数の時系列グラフです。訪問者数グラフと同様の機能を持ちます。

#### その他のグラフ

- `html_timeline.png` - HTML取得のタイムライン（累積取得回数）
- `daily_html_count.png` - 日別のHTML取得数
- `hourly_distribution.png` - 時間帯別のHTML取得分布

### データ管理

- **`graphs/html_data.csv`**: すべてのデータ（HTMLデータと手動データ）を管理
  - HTMLファイルから自動抽出されたデータ
  - 手動で入力したスクリーンショットのデータ（`.png`ファイル名で識別）
  - 同じ`filename`と`date_str`の組み合わせがある場合、新しいデータで上書き

- **`events.json`**: イベント情報を管理
  - 日時、説明、色、線のスタイルを指定可能
  - 各イベントごとに薄さ（透明度）を調整可能

## ファイル構成

```
cluster-ipteca-screenshot-bot/
├── take_screenshot.py          # スクリーンショット取得スクリプト
├── fetch_html.py               # HTML取得スクリプト
├── notify_discord.py           # Discord通知スクリプト
├── notify_graphs_discord.py   # グラフをDiscordに送信
├── analyze_html.py             # HTML解析・グラフ作成スクリプト
├── config.json                 # 設定ファイル
├── events.json                 # イベント情報管理ファイル
├── screenshots/                # スクリーンショット保存ディレクトリ（Gitにコミットされる）
├── html/                       # HTML保存ディレクトリ（Gitにコミットされる）
├── graphs/                     # グラフ保存ディレクトリ
│   ├── html_data.csv          # データ管理用CSV（HTMLデータと手動データ）
│   ├── zone_visitors_timeline.png  # 各ゾーン来場者数の推移グラフ
│   ├── zone_likes_timeline.png    # 各ゾーンいいね数の推移グラフ
│   ├── html_timeline.png          # HTML取得タイムライン
│   ├── daily_html_count.png       # 日別取得数
│   └── hourly_distribution.png    # 時間帯別分布
└── .github/
    └── workflows/
        ├── Production_Screenshot_Notify.yml    # スクリーンショット取得・通知（本番）
        └── Production_Analyze_HTML.yml         # HTML解析・グラフ作成（本番）
```

## 依存関係

- **take_screenshot.py**: `playwright`
- **fetch_html.py**: `playwright`, `beautifulsoup4`
- **notify_discord.py**: `requests`
- **notify_graphs_discord.py**: `requests`
- **analyze_html.py**: `pandas`, `matplotlib`, `beautifulsoup4`

### インストール

```bash
pip install playwright requests pandas matplotlib beautifulsoup4
python -m playwright install --with-deps chromium
```

## 手動データの入力方法

HTMLが取得できない期間のデータを手動で入力する場合：

1. `graphs/html_data.csv`を開く
2. 以下の形式で新しい行を追加：

```csv
filename,date_str,date_only,time_only,hour,file_date_str,file_path,エントランス_visitors,エントランス_likes,メインロビー_visitors,メインロビー_likes,研究成果・技術内容_visitors,研究成果・技術内容_likes,CSAP_visitors,CSAP_likes,地域貢献・展開_visitors,地域貢献・展開_likes,ものづくり教育_visitors,ものづくり教育_likes
IPTeCA_20251119_083317_JST.png,2025/11/19 8:33,2025/11/19,8:33:17,8,,screenshots/IPTeCA_20251119_083317_JST.png,223,1,167,0,92,0,38,0,40,0,69,0
```

3. `analyze_html.py`を実行すると、手動データもグラフに反映されます

## イベント情報の追加方法

グラフにイベント情報を重畳表示する場合：

1. `events.json`を開く
2. `events`配列に新しいイベントを追加：

```json
{
  "date": "2025-11-25 16:30:00",
  "description": "メタバース文化論の授業で展示会訪問",
  "color": "red",
  "linestyle": "dashed",
  "linewidth": 2,
  "alpha": 0.7,
  "line_alpha": 0.35,
  "text_alpha": 0.7,
  "text_color_lightness": 0.7
}
```

3. `analyze_html.py`を実行すると、イベントがグラフに表示されます

### イベントのパラメータ

- `date`: イベントの日時（`YYYY-MM-DD HH:MM:SS`形式）
- `description`: イベントの説明
- `color`: 線とテキストの色（例: `"red"`, `"blue"`）
- `linestyle`: 線のスタイル（`"solid"`, `"dashed"`, `"dotted"`など）
- `linewidth`: 線の太さ
- `alpha`: 基本の透明度（0.0-1.0）
- `line_alpha`: 線の透明度（0.0-1.0、指定しない場合は`alpha * 0.5`）
- `text_alpha`: テキストの透明度（0.0-1.0、デフォルト: 0.7）
- `text_color_lightness`: テキストの色の薄さ（0.0-1.0、大きいほど薄い、デフォルト: 0.7）

## トラブルシューティング

### Discord通知が送信されない

- `DISCORD_WEBHOOK_URL` がGitHub Secretsに設定されているか確認
- `config.json` の `notification.enable_notify` が `true` か確認
- ワークフローの実行ログでエラーメッセージを確認

### スクリーンショットが取得できない

- 対象URLがアクセス可能か確認
- Playwrightのインストールが正常か確認
- ワークフローの実行ログでエラーメッセージを確認

### グラフが作成されない

- `html/`フォルダにHTMLファイルが存在するか確認
- `analyze_html.py`の実行ログでエラーメッセージを確認
- 必要なライブラリ（`pandas`, `matplotlib`, `beautifulsoup4`）がインストールされているか確認

### イベントが表示されない

- `events.json`の形式が正しいか確認
- 日時の形式が`YYYY-MM-DD HH:MM:SS`になっているか確認
- `analyze_html.py`の実行ログでイベント読み込みのメッセージを確認

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。
