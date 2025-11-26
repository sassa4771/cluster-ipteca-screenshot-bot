import os
import sys
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


def send_discord(title: str, body_md: str):
    """DiscordにWebhookで通知を送信"""
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        error_msg = "エラー: DISCORD_WEBHOOK_URL が設定されていません。通知を送信できません。"
        print(error_msg)
        print("GitHub Secrets に DISCORD_WEBHOOK_URL を設定してください。")
        sys.exit(1)
    
    # Discordのメッセージ形式: **title**\nbody_md
    content = f"**{title}**\n{body_md}"
    
    payload = {
        "content": content
    }
    
    try:
        r = requests.post(webhook_url, json=payload, timeout=10)
        # Discordは200または204を返す
        if r.status_code in [200, 204]:
            print(f"Discord通知を送信しました。ステータスコード: {r.status_code}")
        else:
            print(f"Discord通知で予期しないステータスコード: {r.status_code}")
            print(f"レスポンス: {r.text}")
    except Exception as e:
        print(f"Discord通知でエラーが発生しました: {e}")


def send_teams(title: str, body_md: str):
    """Teamsに通知を送信（将来対応）"""
    # TODO: 将来Teams対応する場合に実装
    webhook_url = os.environ.get("TEAMS_WORKFLOW_URL")
    if not webhook_url:
        error_msg = "エラー: TEAMS_WORKFLOW_URL が設定されていません。通知を送信できません。"
        print(error_msg)
        print("GitHub Secrets に TEAMS_WORKFLOW_URL を設定してください。")
        sys.exit(1)
    
    print("Teams通知は未実装です。")
    # 将来的な実装予定
    # message = {
    #     "attachments": [
    #         {
    #             "contentType": "application/vnd.microsoft.card.adaptive",
    #             "content": {
    #                 "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
    #                 "type": "AdaptiveCard",
    #                 "version": "1.2",
    #                 "body": [
    #                     {
    #                         "type": "TextBlock",
    #                         "text": f"## {title}\n\n{body_md}",
    #                         "wrap": True,
    #                         "markdown": True
    #                     }
    #                 ]
    #             }
    #         }
    #     ]
    # }
    # requests.post(webhook_url, json=message, timeout=10)


def send_notify(title: str, body_md: str, config: dict):
    """通知を送信（enable_notify=falseの場合はダミー出力のみ）"""
    notification_config = config["notification"]
    enable_notify = notification_config["enable_notify"]
    target = notification_config.get("target", "discord")
    
    if not enable_notify:
        # 今は通知を無効化している状態。ログにダミー出力のみ。
        print("=== 通知は現在無効化されています ===")
        print(f"[Target] {target}")
        print(f"[Dummy Title] {title}")
        print(f"[Dummy Body]\n{body_md}")
        print("=====================================")
        return
    
    # targetに応じて分岐
    if target == "discord":
        send_discord(title, body_md)
    elif target == "teams":
        send_teams(title, body_md)
    else:
        error_msg = f"エラー: 不明な通知ターゲット: {target}。通知を送信できません。"
        print(error_msg)
        print("config.json の notification.target を 'discord' または 'teams' に設定してください。")
        sys.exit(1)


def check_result():
    """スクリーンショットの存在と更新時刻をチェックし、必要なら通知"""
    config = load_config()
    screenshot_config = config["screenshot"]
    notification_config = config["notification"]
    
    save_dir = screenshot_config["save_dir"]
    time_window_sec = notification_config["time_window_sec"]
    
    # 最新ファイルを取得
    latest_file = get_latest_screenshot(save_dir)
    
    if latest_file is None:
        # ファイルが一つも無ければ「失敗（ファイルなし）」扱い
        title = "Clusterスクリーンショット監視：失敗（新しいファイルなし）"
        body_md = "スクリーンショットファイルが見つかりませんでした。"
        send_notify(title, body_md, config)
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
    
    send_notify(title, body_md, config)


if __name__ == "__main__":
    check_result()
