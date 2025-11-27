import os
import sys
import requests
from datetime import datetime
from zoneinfo import ZoneInfo


def send_discord_with_files(title: str, body_md: str, image_paths: list = None):
    """DiscordにWebhookで通知を送信（複数画像添付可能）"""
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        error_msg = "エラー: DISCORD_WEBHOOK_URL が設定されていません。通知を送信できません。"
        print(error_msg)
        print("GitHub Secrets に DISCORD_WEBHOOK_URL を設定してください。")
        sys.exit(1)
    
    # Discordのメッセージ形式: **title**\nbody_md
    content = f"**{title}**\n{body_md}"
    
    try:
        # 画像ファイルがある場合はmultipart/form-dataで送信
        if image_paths and len(image_paths) > 0:
            files = {}
            for i, image_path in enumerate(image_paths):
                if os.path.exists(image_path):
                    files[f"file{i}"] = (os.path.basename(image_path), open(image_path, "rb"), "image/png")
            
            if files:
                data = {
                    "content": content
                }
                r = requests.post(webhook_url, files=files, data=data, timeout=60)
                # ファイルを閉じる
                for f in files.values():
                    f[1].close()
            else:
                # 画像がない場合は通常のJSON送信
                payload = {
                    "content": content
                }
                r = requests.post(webhook_url, json=payload, timeout=10)
        else:
            # 画像がない場合は通常のJSON送信
            payload = {
                "content": content
            }
            r = requests.post(webhook_url, json=payload, timeout=10)
        
        # Discordは200または204を返す
        if r.status_code in [200, 204]:
            if image_paths:
                print(f"Discord通知を送信しました（画像 {len(image_paths)} 枚添付あり）。ステータスコード: {r.status_code}")
            else:
                print(f"Discord通知を送信しました。ステータスコード: {r.status_code}")
            return True
        else:
            print(f"Discord通知で予期しないステータスコード: {r.status_code}")
            print(f"レスポンス: {r.text}")
            sys.exit(1)
    except Exception as e:
        print(f"Discord通知でエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def notify_graphs():
    """グラフをDiscordに送信"""
    graphs_dir = "graphs"
    visitors_graph = os.path.join(graphs_dir, "zone_visitors_timeline.png")
    likes_graph = os.path.join(graphs_dir, "zone_likes_timeline.png")
    
    # 日本時間（JST）で現在時刻を取得
    jst = ZoneInfo("Asia/Tokyo")
    now_jst = datetime.now(jst)
    timestamp_str = now_jst.strftime("%Y年%m月%d日 %H:%M:%S JST")
    
    title = "IPTeCA グラフ分析結果"
    body_md = (
        f"各ゾーンの来場者数といいね数の推移グラフを生成しました。\n\n"
        f"- **生成時刻**: {timestamp_str}\n"
        f"- **来場者数グラフ**: `zone_visitors_timeline.png`\n"
        f"- **いいね数グラフ**: `zone_likes_timeline.png`"
    )
    
    image_paths = []
    if os.path.exists(visitors_graph):
        image_paths.append(visitors_graph)
    if os.path.exists(likes_graph):
        image_paths.append(likes_graph)
    
    if not image_paths:
        print("警告: グラフファイルが見つかりませんでした。")
        body_md += "\n\n⚠️ グラフファイルが見つかりませんでした。"
        send_discord_with_files(title, body_md, image_paths=None)
        return
    
    send_discord_with_files(title, body_md, image_paths=image_paths)


if __name__ == "__main__":
    try:
        notify_graphs()
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

