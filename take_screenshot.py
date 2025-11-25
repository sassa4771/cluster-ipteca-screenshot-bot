import os
from datetime import datetime
import traceback
import requests  # Teams通知用（関数内で使用、現在は呼び出し無効化）
from playwright.sync_api import sync_playwright

URL = "https://cluster.mu/search?q=IPTeCA&type=world"
SAVE_DIR = "screenshots"
TEAMS_WEBHOOK_URL = None  # os.environ.get("TEAMS_WEBHOOK_URL")  # GitHub Secrets から渡す（現在は無効化）


def send_teams_message(title: str, text: str):
    """Teams に簡易メッセージを送信"""
    if not TEAMS_WEBHOOK_URL:
        print("TEAMS_WEBHOOK_URL が設定されていません。メッセージ: ", title, text)
        return

    payload = {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "summary": title,
        "themeColor": "0076D7",
        "title": title,
        "text": text,
    }

    try:
        r = requests.post(TEAMS_WEBHOOK_URL, json=payload, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print("Teams通知でエラーが発生しました:", e)


def take_screenshot():
    os.makedirs(SAVE_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL)
        page.wait_for_load_state("networkidle")

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_UTC")
        filename = f"{SAVE_DIR}/IPTeCA_{timestamp}.png"
        page.screenshot(path=filename, full_page=True)
        browser.close()

    return filename


def run():
    try:
        filename = take_screenshot()
        msg_title = "Cluster検索スクリーンショット取得：✅ 成功"
        msg_text = f"スクリーンショットを取得しました。\n\n`{filename}`"
        # send_teams_message(msg_title, msg_text)  # Teams通知（現在は無効化）
        print(msg_title, filename)
    except Exception:
        err = traceback.format_exc()
        msg_title = "Cluster検索スクリーンショット取得：❌ エラー"
        msg_text = f"実行中にエラーが発生しました。\n\n```\n{err}\n```"
        # send_teams_message(msg_title, msg_text)  # Teams通知（現在は無効化）
        print(msg_title)
        print(err)
        raise


if __name__ == "__main__":
    run()

