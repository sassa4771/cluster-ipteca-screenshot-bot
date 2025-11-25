import os
import json
import glob
from datetime import datetime, timezone, timedelta
import requests


def load_config():
    """config.json を読み込む"""
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def get_latest_screenshot(save_dir):
    """save_dir 以下の *.png ファイルを列挙して最新ファイルを取得"""
    pattern = os.path.join(save_dir, "*.png")
    files = glob.glob(pattern)
    
    if not files:
        return None
    
    # 最新ファイルを取得（mtimeでソート）
    latest_file = max(files, key=os.path.getmtime)
    return latest_file


def get_jst_timezone():
    """JST（UTC+9）のtimezoneを取得"""
    return timezone(timedelta(hours=9))


def format_iso_jst(dt_utc):
    """UTC時刻をJSTのISO形式文字列に変換"""
    jst = get_jst_timezone()
    dt_jst = dt_utc.replace(tzinfo=timezone.utc).astimezone(jst)
    return dt_jst.isoformat()


def send_teams_card(title: str, body_md: str, enable_notify: bool, notification_config: dict):
    """Teams にアダプティブカード形式で通知を送信（enable_notify=falseの場合はダミー出力のみ）"""
    if not enable_notify:
        # 今は通知を無効化している状態。ログにダミー出力のみ。
        print("=== Teams通知は現在無効化されています ===")
        print(f"[Dummy Title] {title}")
        print(f"[Dummy Body]\n{body_md}")
        print("=====================================")
        return
    
    # 環境変数を優先、なければconfig.jsonの値を使用
    webhook_url = os.environ.get("TEAMS_WORKFLOW_URL") or notification_config.get("teams_workflow_url", "")
    if not webhook_url:
        print("TEAMS_WORKFLOW_URL が設定されていません（環境変数・config.jsonのいずれにも設定なし）。通知をスキップします。")
        return
    
    message = {
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.2",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": f"## {title}\n\n{body_md}",
                            "wrap": True,
                            "markdown": True
                        }
                    ]
                }
            }
        ]
    }
    
    try:
        r = requests.post(webhook_url, json=message, timeout=10)
        r.raise_for_status()
        print(f"Teams通知を送信しました。ステータスコード: {r.status_code}")
    except Exception as e:
        print(f"Teams通知でエラーが発生しました: {e}")


def check_result():
    """スクリーンショットの存在と更新時刻をチェックし、必要なら Teams に通知"""
    config = load_config()
    screenshot_config = config["screenshot"]
    notification_config = config["notification"]
    
    save_dir = screenshot_config["save_dir"]
    time_window_sec = notification_config["time_window_sec"]
    enable_notify = notification_config["enable_notify"]
    
    # 最新ファイルを取得
    latest_file = get_latest_screenshot(save_dir)
    
    if latest_file is None:
        # ファイルが一つも無ければ「失敗（ファイルなし）」扱い
        title = "Clusterスクリーンショット監視：失敗（新しいファイルなし）"
        body_md = "スクリーンショットファイルが見つかりませんでした。"
        send_teams_card(title, body_md, enable_notify, notification_config)
        return
    
    # 最新ファイルの mtime を UTC として取得
    mtime_utc = datetime.utcfromtimestamp(os.path.getmtime(latest_file))
    mtime_utc = mtime_utc.replace(tzinfo=timezone.utc)
    
    # 現在時刻（UTC）との差分秒 age_sec を計算
    now_utc = datetime.now(timezone.utc)
    age_sec = (now_utc - mtime_utc).total_seconds()
    
    # JST 表示用に UTC+9 の timezone を作り、ISO 形式で文字列化
    file_jst_str = format_iso_jst(mtime_utc)
    check_jst_str = format_iso_jst(now_utc)
    
    # 判定
    if age_sec <= time_window_sec:
        # 成功
        title = "Clusterスクリーンショット監視：成功"
        body_md = (
            f"スクリーンショットが正常に取得されています。\n\n"
            f"- **ファイル**: `{latest_file}`\n"
            f"- **取得時刻（JST）**: {file_jst_str}\n"
            f"- **チェック時刻（JST）**: {check_jst_str}\n"
            f"- **経過時間**: {int(age_sec)}秒"
        )
    else:
        # 失敗（新しいファイルが無い）
        title = "Clusterスクリーンショット監視：失敗（新しいファイルなし）"
        body_md = (
            f"最新のスクリーンショットが {time_window_sec} 秒以内に作成されていません。\n\n"
            f"- **ファイル**: `{latest_file}`\n"
            f"- **取得時刻（JST）**: {file_jst_str}\n"
            f"- **チェック時刻（JST）**: {check_jst_str}\n"
            f"- **経過時間**: {int(age_sec)}秒（閾値: {time_window_sec}秒）"
        )
    
    send_teams_card(title, body_md, enable_notify, notification_config)


if __name__ == "__main__":
    check_result()

