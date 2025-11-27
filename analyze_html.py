import os
import sys
import json
import glob
import re
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager
from bs4 import BeautifulSoup

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


# ゾーン名の定義
ZONE_NAMES = [
    "01.IPTeCAバーチャル・イノベーション展示館：エントランス",
    "02.IPTeCAバーチャル・イノベーション展示館：メインロビー",
    "03.IPTeCAバーチャル・イノベーション展示館：「研究成果・技術内容」ゾーン",
    "04.IPTeCAバーチャル・イノベーション展示館：「CSAP」ゾーン",
    "05.IPTeCAバーチャル・イノベーション展示館：「地域貢献・展開」ゾーン",
    "06.IPTeCAバーチャル・イノベーション展示館：「ものづくり教育」ゾーン",
]

ZONE_SHORT_NAMES = [
    "エントランス",
    "メインロビー",
    "研究成果・技術内容",
    "CSAP",
    "地域貢献・展開",
    "ものづくり教育",
]


def extract_zone_data_from_html(html_path):
    """HTMLファイルから各ゾーンの来場者数といいね数を抽出"""
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, "html.parser")
        
        # データを格納する辞書
        zone_data = {}
        
        # ワールドリストのコンテナを探す
        # 実際のHTMLでは <div class="sc-hVAhbL dCaYTa"> がワールドのリスト
        world_list = soup.find("div", class_=lambda x: x and "sc-hVAhbL" in str(x) and "dCaYTa" in str(x))
        
        if not world_list:
            # フォールバック: ワールドの検索結果を含むdivを探す
            world_list = soup.find("div", class_=lambda x: x and "dCaYTa" in str(x))
        
        if not world_list:
            print(f"警告: ワールドリストのコンテナが見つかりませんでした")
            return {}
        
        # ワールドリスト内の各spanタグ（ワールドエントリ）を取得
        world_entries = world_list.find_all("span", recursive=False)
        
        # 各ワールドエントリからデータを抽出
        for entry in world_entries:
            # ゾーン名を取得: divタグのclass="sc-bHxkSF sc-hWnafN dkgfSI jwSkg"
            zone_name_div = entry.find("div", class_=lambda x: x and "sc-bHxkSF" in str(x) and "jwSkg" in str(x))
            
            if not zone_name_div:
                # フォールバック: ゾーン名を含むdivを探す
                zone_name_div = entry.find("div", class_=lambda x: x and "jwSkg" in str(x))
            
            if not zone_name_div:
                continue
            
            zone_name_text = zone_name_div.get_text(strip=True)
            
            # ゾーン名から短い名前を抽出（例：「02.IPTeCAバーチャル・イノベーション展示館：メインロビー」→「メインロビー」）
            matched_zone = None
            for short_name in ZONE_SHORT_NAMES:
                if short_name in zone_name_text:
                    matched_zone = short_name
                    break
            
            if not matched_zone:
                continue
            
            # いいね数を取得: divタグのclass="sc-gFSHlz liSAWz"の下のspanタグ
            likes_div = entry.find("div", class_=lambda x: x and "sc-gFSHlz" in str(x) and "liSAWz" in str(x))
            likes = 0
            if likes_div:
                likes_span = likes_div.find("span")
                if likes_span:
                    likes_text = likes_span.get_text(strip=True)
                    # 数値を抽出（カンマ区切りの可能性がある）
                    likes_match = re.search(r'[\d,]+', likes_text.replace(',', ''))
                    if likes_match:
                        likes = int(likes_match.group().replace(',', ''))
            
            # 訪問回数を取得: divタグのclass="sc-gsZtZH idzaML"の下のspanタグ
            visitors_div = entry.find("div", class_=lambda x: x and "sc-gsZtZH" in str(x) and "idzaML" in str(x))
            visitors = 0
            if visitors_div:
                visitors_span = visitors_div.find("span")
                if visitors_span:
                    visitors_text = visitors_span.get_text(strip=True)
                    # 数値を抽出（カンマ区切りの可能性がある）
                    visitors_match = re.search(r'[\d,]+', visitors_text.replace(',', ''))
                    if visitors_match:
                        visitors = int(visitors_match.group().replace(',', ''))
            
            zone_data[matched_zone] = {
                "visitors": visitors,
                "likes": likes
            }
        
        return zone_data
    except Exception as e:
        print(f"警告: HTMLファイル {html_path} からのデータ抽出に失敗しました: {e}")
        import traceback
        traceback.print_exc()
        return {}


def get_html_files(html_dir):
    """htmlフォルダ内のHTMLファイルを取得し、日時情報とゾーンデータを抽出"""
    pattern = os.path.join(html_dir, "*.html")
    files = glob.glob(pattern)
    
    data = []
    jst = ZoneInfo("Asia/Tokyo")
    
    for file_path in files:
        filename = os.path.basename(file_path)
        # IPTeCA_YYYYMMDD_HHMMSS_JST.html 形式から日時を抽出
        try:
            # ファイル名から日時部分を抽出
            if filename.startswith("IPTeCA_") and filename.endswith("_JST.html"):
                timestamp_str = filename.replace("IPTeCA_", "").replace("_JST.html", "")
                # YYYYMMDD_HHMMSS 形式をパース
                dt = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                # JSTとして設定
                dt = dt.replace(tzinfo=jst)
                
                # ファイルの作成日時も取得
                mtime = os.path.getmtime(file_path)
                file_dt = datetime.fromtimestamp(mtime, tz=jst)
                
                # HTMLからゾーンデータを抽出
                zone_data = extract_zone_data_from_html(file_path)
                
                file_data = {
                    "filename": filename,
                    "date": dt,
                    "file_date": file_dt,
                    "file_path": file_path
                }
                
                # 各ゾーンのデータを追加
                for zone_name in ZONE_SHORT_NAMES:
                    file_data[f"{zone_name}_visitors"] = zone_data.get(zone_name, {}).get("visitors", 0)
                    file_data[f"{zone_name}_likes"] = zone_data.get(zone_name, {}).get("likes", 0)
                
                data.append(file_data)
        except Exception as e:
            print(f"警告: ファイル {filename} の解析に失敗しました: {e}")
            continue
    
    return data


def create_timeline_graph(data, output_dir):
    """HTML取得のタイムライングラフを作成"""
    if not data:
        print("グラフを作成するデータがありません。")
        return None
    
    df = pd.DataFrame(data)
    df = df.sort_values("date")
    
    plt.figure(figsize=(12, 6))
    plt.plot(df["date"], range(len(df)), marker="o", linestyle="-", markersize=8)
    plt.xlabel("日時 (JST)", fontsize=16, fontweight="bold")
    plt.ylabel("HTML取得回数（累積）", fontsize=16, fontweight="bold")
    plt.title("IPTeCA HTML取得タイムライン", fontsize=18, fontweight="bold")
    plt.xticks(rotation=45, ha="right", fontsize=14, fontweight="bold")
    plt.yticks(fontsize=14, fontweight="bold")
    plt.grid(True, alpha=0.3, linewidth=1.5)
    plt.tight_layout()
    
    # グラフを保存
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "html_timeline.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    
    print(f"タイムライングラフを保存しました: {output_path}")
    return output_path


def create_daily_count_graph(data, output_dir):
    """日別のHTML取得数をグラフ化"""
    if not data:
        print("グラフを作成するデータがありません。")
        return None
    
    df = pd.DataFrame(data)
    df["date_only"] = df["date"].dt.date
    
    daily_counts = df.groupby("date_only").size().reset_index(name="count")
    daily_counts = daily_counts.sort_values("date_only")
    
    plt.figure(figsize=(10, 5))
    plt.bar(daily_counts["date_only"], daily_counts["count"], color="steelblue", alpha=0.7)
    plt.xlabel("日付", fontsize=16, fontweight="bold")
    plt.ylabel("取得回数", fontsize=16, fontweight="bold")
    plt.title("IPTeCA HTML取得数（日別）", fontsize=18, fontweight="bold")
    plt.xticks(rotation=45, ha="right", fontsize=14, fontweight="bold")
    plt.yticks(fontsize=14, fontweight="bold")
    plt.grid(True, alpha=0.3, axis="y", linewidth=1.5)
    plt.tight_layout()
    
    # グラフを保存
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "daily_html_count.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    
    print(f"日別取得数グラフを保存しました: {output_path}")
    return output_path


def create_hourly_distribution_graph(data, output_dir):
    """時間帯別のHTML取得分布をグラフ化"""
    if not data:
        print("グラフを作成するデータがありません。")
        return None
    
    df = pd.DataFrame(data)
    df["hour"] = df["date"].dt.hour
    
    hourly_counts = df.groupby("hour").size().reset_index(name="count")
    hourly_counts = hourly_counts.sort_values("hour")
    
    plt.figure(figsize=(10, 5))
    plt.bar(hourly_counts["hour"], hourly_counts["count"], color="coral", alpha=0.7)
    plt.xlabel("時間帯 (JST)", fontsize=16, fontweight="bold")
    plt.ylabel("取得回数", fontsize=16, fontweight="bold")
    plt.title("IPTeCA HTML取得数（時間帯別）", fontsize=18, fontweight="bold")
    plt.xticks(range(0, 24), [f"{h:02d}:00" for h in range(24)], rotation=45, ha="right", fontsize=14, fontweight="bold")
    plt.yticks(fontsize=14, fontweight="bold")
    plt.grid(True, alpha=0.3, axis="y", linewidth=1.5)
    plt.tight_layout()
    
    # グラフを保存
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "hourly_distribution.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    
    print(f"時間帯別分布グラフを保存しました: {output_path}")
    return output_path


def create_zone_visitors_graph(data, output_dir):
    """各ゾーンの来場者数の時系列グラフを作成"""
    if not data:
        print("グラフを作成するデータがありません。")
        return None
    
    df = pd.DataFrame(data)
    df = df.sort_values("date")
    
    fig, ax = plt.subplots(figsize=(16, 10))
    
    for zone_name in ZONE_SHORT_NAMES:
        col_name = f"{zone_name}_visitors"
        if col_name in df.columns:
            ax.plot(df["date"], df[col_name], marker="o", label=zone_name, linewidth=2.5, markersize=8)
    
    ax.set_xlabel("日時 (JST)", fontsize=20, fontweight="bold")
    ax.set_ylabel("来場者数", fontsize=20, fontweight="bold")
    ax.set_title("IPTeCA 各ゾーン来場者数の推移", fontsize=22, fontweight="bold")
    ax.tick_params(axis='x', rotation=45, labelsize=18)
    ax.tick_params(axis='x', which='major', labelsize=18, labelcolor='black')
    # 縦軸は整数のみ
    y_min, y_max = ax.get_ylim()
    y_ticks = np.arange(int(y_min), int(y_max) + 1, max(1, int((y_max - y_min) / 10)))
    ax.set_yticks(y_ticks)
    ax.tick_params(axis='y', labelsize=18, labelcolor='black')
    # 凡例をx軸のタイトルの下に配置（さらに下に）
    legend_font = font_manager.FontProperties(weight='bold', size=18)
    ax.legend(bbox_to_anchor=(0.5, -0.2), loc='upper center', ncol=3, prop=legend_font, frameon=True)
    ax.grid(True, alpha=0.3, linewidth=1.5)
    # 余白を調整して凡例が重ならないようにする
    plt.subplots_adjust(bottom=0.25)
    plt.tight_layout()
    
    # グラフを保存
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "zone_visitors_timeline.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    
    print(f"ゾーン来場者数グラフを保存しました: {output_path}")
    return output_path


def create_zone_likes_graph(data, output_dir):
    """各ゾーンのいいね数の時系列グラフを作成"""
    if not data:
        print("グラフを作成するデータがありません。")
        return None
    
    df = pd.DataFrame(data)
    df = df.sort_values("date")
    
    fig, ax = plt.subplots(figsize=(16, 10))
    
    for zone_name in ZONE_SHORT_NAMES:
        col_name = f"{zone_name}_likes"
        if col_name in df.columns:
            ax.plot(df["date"], df[col_name], marker="s", label=zone_name, linewidth=2.5, markersize=8)
    
    ax.set_xlabel("日時 (JST)", fontsize=20, fontweight="bold")
    ax.set_ylabel("いいね数", fontsize=20, fontweight="bold")
    ax.set_title("IPTeCA 各ゾーンいいね数の推移", fontsize=22, fontweight="bold")
    ax.tick_params(axis='x', rotation=45, labelsize=18)
    ax.tick_params(axis='x', which='major', labelsize=18, labelcolor='black')
    # 縦軸は整数のみ
    y_min, y_max = ax.get_ylim()
    y_ticks = np.arange(int(y_min), int(y_max) + 1, max(1, int((y_max - y_min) / 10)))
    ax.set_yticks(y_ticks)
    ax.tick_params(axis='y', labelsize=18, labelcolor='black')
    # 凡例をx軸のタイトルの下に配置（さらに下に）
    legend_font = font_manager.FontProperties(weight='bold', size=18)
    ax.legend(bbox_to_anchor=(0.5, -0.2), loc='upper center', ncol=3, prop=legend_font, frameon=True)
    ax.grid(True, alpha=0.3, linewidth=1.5)
    # 余白を調整して凡例が重ならないようにする
    plt.subplots_adjust(bottom=0.25)
    plt.tight_layout()
    
    # グラフを保存
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "zone_likes_timeline.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    
    print(f"ゾーンいいね数グラフを保存しました: {output_path}")
    return output_path


def save_to_csv(data, output_dir, csv_path):
    """HTML情報をCSVに保存（追記形式）"""
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
    
    # CSV用の列を選択（ゾーンデータも含める）
    base_columns = ["filename", "date_str", "date_only", "time_only", "hour", "file_date_str", "file_path"]
    zone_columns = []
    for zone_name in ZONE_SHORT_NAMES:
        zone_columns.extend([f"{zone_name}_visitors", f"{zone_name}_likes"])
    
    csv_columns = base_columns + zone_columns
    # 存在する列のみを選択
    available_columns = [col for col in csv_columns if col in df_new.columns]
    df_new_output = df_new[available_columns].copy()
    
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
    """CSVファイルからHTML情報を読み込む"""
    if not os.path.exists(csv_path):
        print(f"エラー: CSVファイルが見つかりません: {csv_path}")
        return None
    
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    jst = ZoneInfo("Asia/Tokyo")
    
    # 日時文字列をdatetimeオブジェクトに変換
    df["date"] = pd.to_datetime(df["date_str"]).dt.tz_localize(jst)
    df["file_date"] = pd.to_datetime(df["file_date_str"]).dt.tz_localize(jst)
    
    # データ形式を統一（ゾーンデータも含める）
    data = []
    for _, row in df.iterrows():
        row_data = {
            "filename": row["filename"],
            "date": row["date"],
            "file_date": row["file_date"],
            "file_path": row["file_path"]
        }
        
        # ゾーンデータを追加
        for zone_name in ZONE_SHORT_NAMES:
            visitors_col = f"{zone_name}_visitors"
            likes_col = f"{zone_name}_likes"
            if visitors_col in df.columns:
                row_data[visitors_col] = row.get(visitors_col, 0)
            if likes_col in df.columns:
                row_data[likes_col] = row.get(likes_col, 0)
        
        data.append(row_data)
    
    return data


def analyze_html():
    """HTMLファイルを解析してグラフを作成"""
    html_dir = "html"
    output_dir = "graphs"
    csv_path = os.path.join(output_dir, "html_data.csv")
    
    # 日本語フォントを設定
    setup_japanese_font()
    
    # HTMLファイルを取得
    print(f"htmlフォルダをスキャン中: {html_dir}")
    data = get_html_files(html_dir)
    
    if not data:
        print(f"エラー: {html_dir} フォルダにHTMLファイルが見つかりませんでした。")
        sys.exit(1)
    
    print(f"HTMLファイルを {len(data)} 件見つけました。")
    
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
    
    # ゾーンデータのグラフを作成
    create_zone_visitors_graph(data, output_dir)
    create_zone_likes_graph(data, output_dir)
    
    print(f"\nすべてのグラフとCSVを {output_dir}/ フォルダに保存しました。")


if __name__ == "__main__":
    try:
        analyze_html()
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

