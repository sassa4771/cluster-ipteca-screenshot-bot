import os
import sys
import json
import glob
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager

# 日本語フォントの設定
def setup_japanese_font():
    """日本語フォントを設定する"""
    font_path = "NotoSansJP-VariableFont_wght.ttf"
    
    try:
        if os.path.exists(font_path):
            # リポジトリに配置されたフォントファイルを使用
            font_manager.fontManager.addfont(font_path)
            font_prop = font_manager.FontProperties(fname=font_path)
            plt.rcParams["font.family"] = font_prop.get_name()
            print(f"日本語フォントを設定しました: {font_prop.get_name()} ({font_path})")
        else:
            # フォントファイルが見つからない場合、システムフォントを探す
            print(f"警告: {font_path} が見つかりません。システムフォントを検索します...")
            font_list = font_manager.findSystemFonts()
            japanese_fonts = []
            for sys_font_path in font_list:
                try:
                    font_name = font_manager.get_font(sys_font_path).family_name
                    if 'Noto' in font_name or 'Sans' in font_name or 'JP' in font_name:
                        japanese_fonts.append(sys_font_path)
                except:
                    pass
            
            if japanese_fonts:
                # 最初に見つかったフォントを使用
                sys_font_path = japanese_fonts[0]
                font_manager.fontManager.addfont(sys_font_path)
                font_prop = font_manager.FontProperties(fname=sys_font_path)
                plt.rcParams["font.family"] = font_prop.get_name()
                print(f"システムフォントを使用しました: {font_prop.get_name()}")
            else:
                # フォールバック: デフォルトフォントを使用
                plt.rcParams["font.family"] = "DejaVu Sans"
                print("警告: 日本語フォントが見つかりませんでした。デフォルトフォントを使用します。")
    except Exception as e:
        print(f"フォント設定でエラーが発生しました: {e}")
        plt.rcParams["font.family"] = "DejaVu Sans"


def load_config():
    """config.json を読み込む"""
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def get_screenshot_files(save_dir):
    """screenshotsフォルダ内の画像ファイルを取得し、日時情報を抽出"""
    pattern = os.path.join(save_dir, "*.png")
    files = glob.glob(pattern)
    
    data = []
    jst = ZoneInfo("Asia/Tokyo")
    
    for file_path in files:
        filename = os.path.basename(file_path)
        # IPTeCA_YYYYMMDD_HHMMSS_JST.png 形式から日時を抽出
        try:
            # ファイル名から日時部分を抽出
            if filename.startswith("IPTeCA_") and filename.endswith("_JST.png"):
                timestamp_str = filename.replace("IPTeCA_", "").replace("_JST.png", "")
                # YYYYMMDD_HHMMSS 形式をパース
                dt = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                # JSTとして設定
                dt = dt.replace(tzinfo=jst)
                
                # ファイルの作成日時も取得
                mtime = os.path.getmtime(file_path)
                file_dt = datetime.fromtimestamp(mtime, tz=jst)
                
                data.append({
                    "filename": filename,
                    "date": dt,
                    "file_date": file_dt,
                    "file_path": file_path
                })
        except Exception as e:
            print(f"警告: ファイル {filename} の解析に失敗しました: {e}")
            continue
    
    return data


def create_timeline_graph(data, output_dir):
    """スクリーンショット取得のタイムライングラフを作成"""
    if not data:
        print("グラフを作成するデータがありません。")
        return None
    
    df = pd.DataFrame(data)
    df = df.sort_values("date")
    
    plt.figure(figsize=(12, 6))
    plt.plot(df["date"], range(len(df)), marker="o", linestyle="-", markersize=8)
    plt.xlabel("日時 (JST)", fontsize=12)
    plt.ylabel("スクリーンショット取得回数（累積）", fontsize=12)
    plt.title("IPTeCA スクリーンショット取得タイムライン", fontsize=14, fontweight="bold")
    plt.xticks(rotation=45, ha="right")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # グラフを保存
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "screenshot_timeline.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    
    print(f"タイムライングラフを保存しました: {output_path}")
    return output_path


def create_daily_count_graph(data, output_dir):
    """日別のスクリーンショット取得数をグラフ化"""
    if not data:
        print("グラフを作成するデータがありません。")
        return None
    
    df = pd.DataFrame(data)
    df["date_only"] = df["date"].dt.date
    
    daily_counts = df.groupby("date_only").size().reset_index(name="count")
    daily_counts = daily_counts.sort_values("date_only")
    
    plt.figure(figsize=(10, 5))
    plt.bar(daily_counts["date_only"], daily_counts["count"], color="steelblue", alpha=0.7)
    plt.xlabel("日付", fontsize=12)
    plt.ylabel("取得回数", fontsize=12)
    plt.title("IPTeCA スクリーンショット取得数（日別）", fontsize=14, fontweight="bold")
    plt.xticks(rotation=45, ha="right")
    plt.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    
    # グラフを保存
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "daily_screenshot_count.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    
    print(f"日別取得数グラフを保存しました: {output_path}")
    return output_path


def create_hourly_distribution_graph(data, output_dir):
    """時間帯別の取得分布をグラフ化"""
    if not data:
        print("グラフを作成するデータがありません。")
        return None
    
    df = pd.DataFrame(data)
    df["hour"] = df["date"].dt.hour
    
    hourly_counts = df.groupby("hour").size().reset_index(name="count")
    hourly_counts = hourly_counts.sort_values("hour")
    
    plt.figure(figsize=(10, 5))
    plt.bar(hourly_counts["hour"], hourly_counts["count"], color="coral", alpha=0.7)
    plt.xlabel("時間帯 (JST)", fontsize=12)
    plt.ylabel("取得回数", fontsize=12)
    plt.title("IPTeCA スクリーンショット取得数（時間帯別）", fontsize=14, fontweight="bold")
    plt.xticks(range(0, 24), [f"{h:02d}:00" for h in range(24)], rotation=45, ha="right")
    plt.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    
    # グラフを保存
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "hourly_distribution.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    
    print(f"時間帯別分布グラフを保存しました: {output_path}")
    return output_path


def save_to_csv(data, output_dir, csv_path):
    """スクリーンショット情報をCSVに保存（追記形式）"""
    if not data:
        print("CSVに保存するデータがありません。")
        return None
    
    # 新しいデータをDataFrameに変換
    df_new = pd.DataFrame(data)
    df_new["date_str"] = df_new["date"].dt.strftime("%Y-%m-%d %H:%M:%S")
    df_new["date_only"] = df_new["date"].dt.strftime("%Y-%m-%d")
    df_new["time_only"] = df_new["date"].dt.strftime("%H:%M:%S")
    df_new["hour"] = df_new["date"].dt.hour
    df_new["file_date_str"] = df_new["file_date"].dt.strftime("%Y-%m-%d %H:%M:%S")
    
    # CSV用の列を選択
    csv_columns = ["filename", "date_str", "date_only", "time_only", "hour", "file_date_str", "file_path"]
    df_new_output = df_new[csv_columns].copy()
    
    # 既存のCSVファイルがある場合は読み込む
    if os.path.exists(csv_path):
        print(f"既存のCSVファイルを読み込みます: {csv_path}")
        df_existing = pd.read_csv(csv_path, encoding="utf-8-sig")
        
        # 既存のデータと新しいデータをマージ（重複を除去）
        # filenameとdate_strの組み合わせで重複チェック
        df_combined = pd.concat([df_existing, df_new_output], ignore_index=True)
        df_combined = df_combined.drop_duplicates(subset=["filename", "date_str"], keep="last")
        df_combined = df_combined.sort_values("date_str")
        
        print(f"既存データ: {len(df_existing)} 件、新規データ: {len(df_new_output)} 件、合計: {len(df_combined)} 件")
    else:
        print("既存のCSVファイルが見つかりません。新規作成します。")
        df_combined = df_new_output.sort_values("date_str")
    
    # CSVを保存
    os.makedirs(output_dir, exist_ok=True)
    df_combined.to_csv(csv_path, index=False, encoding="utf-8-sig")
    
    print(f"CSVファイルを保存しました: {csv_path} (合計 {len(df_combined)} 件)")
    return csv_path


def load_from_csv(csv_path):
    """CSVファイルからスクリーンショット情報を読み込む"""
    if not os.path.exists(csv_path):
        print(f"エラー: CSVファイルが見つかりません: {csv_path}")
        return None
    
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    jst = ZoneInfo("Asia/Tokyo")
    
    # 日時文字列をdatetimeオブジェクトに変換
    df["date"] = pd.to_datetime(df["date_str"]).dt.tz_localize(jst)
    df["file_date"] = pd.to_datetime(df["file_date_str"]).dt.tz_localize(jst)
    
    # データ形式を統一
    data = []
    for _, row in df.iterrows():
        data.append({
            "filename": row["filename"],
            "date": row["date"],
            "file_date": row["file_date"],
            "file_path": row["file_path"]
        })
    
    return data


def analyze_screenshots():
    """スクリーンショットを解析してグラフを作成"""
    config = load_config()
    screenshot_config = config["screenshot"]
    save_dir = screenshot_config["save_dir"]
    output_dir = "graphs"
    csv_path = os.path.join(output_dir, "screenshot_data.csv")
    
    # 日本語フォントを設定
    setup_japanese_font()
    
    # スクリーンショットファイルを取得
    print(f"screenshotsフォルダをスキャン中: {save_dir}")
    data = get_screenshot_files(save_dir)
    
    if not data:
        print(f"エラー: {save_dir} フォルダにスクリーンショットファイルが見つかりませんでした。")
        sys.exit(1)
    
    print(f"スクリーンショットファイルを {len(data)} 件見つけました。")
    
    # CSVに保存（追記形式）
    save_to_csv(data, output_dir, csv_path)
    
    # グラフ作成用にCSVから全データを読み込む
    if os.path.exists(csv_path):
        print(f"CSVファイルから全データを読み込みます: {csv_path}")
        data_from_csv = load_from_csv(csv_path)
        if data_from_csv:
            data = data_from_csv
            print(f"CSVから {len(data)} 件のデータを読み込みました。")
    
    # グラフを作成
    create_timeline_graph(data, output_dir)
    create_daily_count_graph(data, output_dir)
    create_hourly_distribution_graph(data, output_dir)
    
    print(f"\nすべてのグラフとCSVを {output_dir}/ フォルダに保存しました。")


if __name__ == "__main__":
    try:
        analyze_screenshots()
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

