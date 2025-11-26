import os
import sys
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright


def load_config():
    """config.json を読み込む"""
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_html():
    """HTMLを取得する"""
    config = load_config()
    screenshot_config = config["screenshot"]
    url = screenshot_config["url"]
    save_dir = "html"  # HTML保存ディレクトリ
    
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
        
        # 日本時間（JST）でYYYYMMDD_HHMMSS_JST形式のタイムスタンプを生成
        jst = ZoneInfo("Asia/Tokyo")
        timestamp = datetime.now(jst).strftime("%Y%m%d_%H%M%S_JST")
        filename = f"{save_dir}/IPTeCA_{timestamp}.html"
        
        # HTMLコンテンツを取得
        html_content = page.content()
        
        # HTMLファイルに保存
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        browser.close()
    
    return filename


if __name__ == "__main__":
    try:
        filename = fetch_html()
        print(f"Saved HTML: {filename}")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

