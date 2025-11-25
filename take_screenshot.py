import os
import json
from datetime import datetime
from playwright.sync_api import sync_playwright


def load_config():
    """config.json を読み込む"""
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def take_screenshot():
    """スクリーンショットを取得する"""
    config = load_config()
    screenshot_config = config["screenshot"]
    url = screenshot_config["url"]
    save_dir = screenshot_config["save_dir"]
    
    # ディレクトリが無ければ作成
    os.makedirs(save_dir, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state("networkidle")
        
        # GitHub Actions は UTC で動くため、YYYYMMDD_HHMMSS_UTC 形式のタイムスタンプを生成
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_UTC")
        filename = f"{save_dir}/IPTeCA_{timestamp}.png"
        page.screenshot(path=filename, full_page=True)
        browser.close()
    
    return filename


if __name__ == "__main__":
    filename = take_screenshot()
    print(f"Saved screenshot: {filename}")
