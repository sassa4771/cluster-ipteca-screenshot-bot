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
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(url)
        page.wait_for_load_state("networkidle")
        
        # Cookieバナーの閉鎖処理
        for selector in ["text=Allow all", "text=すべて許可"]:
            try:
                page.click(selector, timeout=3000)
                break
            except:
                pass
        
        # 下部までスクロールして表示を更新
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1500)
        
        # GitHub Actions は UTC で動くため、YYYYMMDD_HHMMSS_UTC 形式のタイムスタンプを生成
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_UTC")
        filename = f"{save_dir}/IPTeCA_{timestamp}.png"
        page.screenshot(path=filename, full_page=True)
        browser.close()
    
    return filename


if __name__ == "__main__":
    filename = take_screenshot()
    print(f"Saved screenshot: {filename}")
