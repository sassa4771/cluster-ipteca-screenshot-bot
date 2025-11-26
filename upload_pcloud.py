import os
import sys
import json
import glob
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


def upload_to_pcloud(file_path, upload_code, remote_dir):
    """pCloudにファイルをアップロード"""
    url = f"https://api.pcloud.com/uploadtolink?code={upload_code}"
    
    if not os.path.exists(file_path):
        print(f"エラー: ファイルが見つかりません: {file_path}")
        sys.exit(1)
    
    # ファイル名を取得
    filename = os.path.basename(file_path)
    
    # remote_dirが指定されている場合は、パスに含める
    if remote_dir:
        # remote_dirが/で始まっていない場合は追加
        if not remote_dir.startswith("/"):
            remote_dir = "/" + remote_dir
        # ファイル名を結合
        remote_path = f"{remote_dir}/{filename}"
    else:
        remote_path = f"/{filename}"
    
    try:
        # multipart/form-data でアップロード
        with open(file_path, "rb") as f:
            files = {
                "file": (filename, f, "image/png")
            }
            data = {
                "filename": remote_path
            }
            
            print(f"アップロード中: {file_path} -> {remote_path}")
            r = requests.post(url, files=files, data=data, timeout=30)
            
            if r.status_code == 200:
                result = r.json()
                if result.get("result") == 0:
                    print(f"✅ pCloudアップロード成功: {remote_path}")
                    return True
                else:
                    error_msg = result.get("error", "不明なエラー")
                    print(f"❌ pCloudアップロード失敗: {error_msg}")
                    print(f"レスポンス: {r.text}")
                    sys.exit(1)
            else:
                print(f"❌ pCloudアップロード失敗: HTTP {r.status_code}")
                print(f"レスポンス: {r.text}")
                sys.exit(1)
    except Exception as e:
        print(f"❌ pCloudアップロードでエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def upload_latest_screenshot():
    """最新のスクリーンショットをpCloudにアップロード"""
    config = load_config()
    screenshot_config = config["screenshot"]
    pcloud_config = config.get("pcloud", {})
    
    save_dir = screenshot_config["save_dir"]
    enable_upload = pcloud_config.get("enable_upload", False)
    remote_dir = pcloud_config.get("remote_dir", "")
    
    if not enable_upload:
        print("pCloudアップロードは無効化されています。スキップします。")
        return
    
    # PCLOUD_UPLOAD_CODE を環境変数から取得
    upload_code = os.environ.get("PCLOUD_UPLOAD_CODE")
    if not upload_code:
        print("エラー: PCLOUD_UPLOAD_CODE が設定されていません。")
        print("GitHub Secrets に PCLOUD_UPLOAD_CODE を設定してください。")
        sys.exit(1)
    
    # 最新ファイルを取得
    latest_file = get_latest_screenshot(save_dir)
    
    if latest_file is None:
        print("エラー: アップロードするスクリーンショットファイルが見つかりません。")
        sys.exit(1)
    
    # アップロード実行
    upload_to_pcloud(latest_file, upload_code, remote_dir)


if __name__ == "__main__":
    try:
        upload_latest_screenshot()
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

