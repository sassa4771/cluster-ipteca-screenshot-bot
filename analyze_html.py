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
import matplotlib.colors as mcolors
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

# ゾーン番号とゾーン名の対応
ZONE_NUMBERS = {
    "01": "エントランス",
    "02": "メインロビー",
    "03": "研究成果・技術内容",
    "04": "CSAP",
    "05": "地域貢献・展開",
    "06": "ものづくり教育",
}


def extract_zone_data_from_html(html_path):
    """HTMLファイルから各ゾーンの来場者数といいね数を抽出
    SVGアイコン（♥と▶）を基準に数値を取得する（クラス名非依存）"""
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, "html.parser")
        
        # データを格納する辞書
        zone_data = {}
        
        # ワールドカード（a[href^="/w/"]）を全て取得
        world_cards = soup.find_all("a", href=lambda x: x and x.startswith("/w/"))
        
        for card in world_cards:
            # カード内のタイトル要素を探す（最も長いテキストまたは見出し相当のノード）
            name = None
            title_candidates = []
            
            # div内のテキストを候補として収集
            for div in card.find_all("div", recursive=True):
                text = div.get_text(strip=True)
                if text and len(text) > 10:  # 短すぎるテキストは除外
                    title_candidates.append((len(text), text))
            
            if title_candidates:
                # 最も長いテキストをタイトルとして採用
                title_candidates.sort(reverse=True, key=lambda x: x[0])
                name = title_candidates[0][1]
            
            if not name:
                continue
            
            # ゾーン名から短い名前を抽出（例：「02.IPTeCAバーチャル・イノベーション展示館：メインロビー」→「メインロビー」）
            matched_zone = None
            for short_name in ZONE_SHORT_NAMES:
                if short_name in name:
                    matched_zone = short_name
                    break
            
            if not matched_zone:
                continue
            
            # カード内の全てのsvgを走査
            likes = 0
            visitors = 0
            
            svgs = card.find_all("svg", recursive=True)
            for svg in svgs:
                # svg内のpath要素を探す
                paths = svg.find_all("path", recursive=True)
                for path in paths:
                    d_attr = path.get("d", "")
                    
                    # Heart（♥）判定: dが"M60.004"で始まる
                    if d_attr.startswith("M60.004"):
                        # svgの親要素内で、svgの次のspanを探す
                        parent = svg.parent
                        if parent:
                            # 親要素内でsvgの後に来る最初のspanを探す
                            found_span = svg.find_next_sibling("span")
                            
                            # 見つからない場合、親要素内の全てのspanを探す
                            if not found_span:
                                all_spans = parent.find_all("span", recursive=False)
                                # svgの後に来る最初のspanを探す
                                svg_index = None
                                for i, child in enumerate(parent.children):
                                    if child == svg:
                                        svg_index = i
                                        break
                                
                                if svg_index is not None:
                                    for i, child in enumerate(parent.children):
                                        if i > svg_index and child.name == "span":
                                            found_span = child
                                            break
                            
                            if found_span:
                                likes_text = found_span.get_text(strip=True)
                                likes_match = re.search(r'[\d,]+', likes_text.replace(',', ''))
                                if likes_match:
                                    likes = int(likes_match.group().replace(',', ''))
                    
                    # Play（▶）判定: dが"M38.678"で始まる
                    elif d_attr.startswith("M38.678"):
                        # svgの親要素内で、svgの次のspanを探す
                        parent = svg.parent
                        if parent:
                            # 親要素内でsvgの後に来る最初のspanを探す
                            found_span = svg.find_next_sibling("span")
                            
                            # 見つからない場合、親要素内の全てのspanを探す
                            if not found_span:
                                all_spans = parent.find_all("span", recursive=False)
                                # svgの後に来る最初のspanを探す
                                svg_index = None
                                for i, child in enumerate(parent.children):
                                    if child == svg:
                                        svg_index = i
                                        break
                                
                                if svg_index is not None:
                                    for i, child in enumerate(parent.children):
                                        if i > svg_index and child.name == "span":
                                            found_span = child
                                            break
                            
                            if found_span:
                                visitors_text = found_span.get_text(strip=True)
                                visitors_match = re.search(r'[\d,]+', visitors_text.replace(',', ''))
                                if visitors_match:
                                    visitors = int(visitors_match.group().replace(',', ''))
            
            # データが取得できた場合のみ追加
            if matched_zone:
                zone_data[matched_zone] = {
                    "visitors": visitors,
                    "likes": likes
                }
                # デバッグ用：片方しか取れない場合は警告
                if likes == 0 and visitors > 0:
                    print(f"警告: {matched_zone} のいいね数が取得できませんでした（訪問者数: {visitors}）")
                elif visitors == 0 and likes > 0:
                    print(f"警告: {matched_zone} の訪問者数が取得できませんでした（いいね数: {likes}）")
        
        return zone_data
    except Exception as e:
        print(f"警告: HTMLファイル {html_path} からのデータ抽出に失敗しました: {e}")
        import traceback
        traceback.print_exc()
        return {}


def get_html_files(html_dir, screenshots_dir="screenshots"):
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


def load_events(events_path="events.json"):
    """イベント情報をJSONファイルから読み込む"""
    if not os.path.exists(events_path):
        return []
    
    try:
        with open(events_path, "r", encoding="utf-8") as f:
            events_data = json.load(f)
        
        if "events" not in events_data:
            return []
        
        jst = ZoneInfo("Asia/Tokyo")
        events = []
        
        for event in events_data["events"]:
            try:
                # 日時をdatetimeオブジェクトに変換
                event_date = datetime.strptime(event["date"], "%Y-%m-%d %H:%M:%S")
                event_date = event_date.replace(tzinfo=jst)
                
                event_info = {
                    "date": event_date,
                    "description": event.get("description", ""),
                    "color": event.get("color", "red"),
                    "linestyle": event.get("linestyle", "dashed"),
                    "linewidth": event.get("linewidth", 2),
                    "alpha": event.get("alpha", 0.7),
                    "line_alpha": event.get("line_alpha", None),  # 線の透明度（Noneの場合はalpha * 0.5を使用）
                    "text_alpha": event.get("text_alpha", 0.7),  # テキストの透明度
                    "text_color_lightness": event.get("text_color_lightness", 0.7)  # テキストの色の薄さ（0.0-1.0、大きいほど薄い）
                }
                events.append(event_info)
            except Exception as e:
                print(f"警告: イベントの解析に失敗しました: {event}, エラー: {e}")
                continue
        
        return events
    except Exception as e:
        print(f"警告: イベントファイルの読み込みに失敗しました: {e}")
        return []


def add_events_to_graph(ax, events, y_min, y_max):
    """グラフにイベント情報を重畳表示"""
    if not events:
        return
    
    for i, event in enumerate(events):
        event_date = event["date"]
        description = event["description"]
        color = event["color"]
        linestyle = event["linestyle"]
        linewidth = event["linewidth"]
        alpha = event["alpha"]
        line_alpha = event.get("line_alpha")  # 線の透明度（Noneの場合はalpha * 0.5を使用）
        text_alpha = event.get("text_alpha", 0.7)  # テキストの透明度
        text_color_lightness = event.get("text_color_lightness", 0.7)  # テキストの色の薄さ
        
        # 垂直線を描画（透明度をJSONで調整可能）
        if line_alpha is None:
            line_alpha = alpha * 0.5
        ax.axvline(x=event_date, color=color, linestyle=linestyle, 
                   linewidth=linewidth, alpha=line_alpha, zorder=10)
        
        # 日付をフォーマット（例: 2025/11/17 17:00）
        date_str = event_date.strftime("%Y/%m/%d %H:%M")
        
        # テキストに日付と説明を含める
        text = f"{date_str}\n{description}"
        
        # テキストアノテーションを追加（横書き、透明度をJSONで調整可能）
        # イベントが複数ある場合、縦方向にずらして表示
        y_offset = y_max - (y_max - y_min) * 0.15 * (i % 4 + 1)
        
        # 色を薄くする（RGB値を調整、JSONで調整可能）
        if isinstance(color, str):
            rgb = mcolors.to_rgb(color)
        else:
            rgb = color
        # 色を薄くする（白を混ぜる、text_color_lightnessで調整）
        light_color = tuple((1.0 - text_color_lightness) * c + text_color_lightness * 1.0 for c in rgb)
        
        ax.annotate(
            text,
            xy=(event_date, y_offset),
            xytext=(10, 10),
            textcoords="offset points",
            fontsize=10,
            fontweight="normal",
            color=light_color,
            bbox=dict(boxstyle="round,pad=0.5", facecolor="white", edgecolor=light_color, alpha=text_alpha, linewidth=1.0),
            arrowprops=dict(arrowstyle="->", color=light_color, lw=1.0, alpha=text_alpha * 0.85),
            rotation=0,
            ha="left",
            va="bottom"
        )


def create_zone_visitors_graph(data, output_dir, events=None):
    """各ゾーンの来場者数の時系列グラフを作成し、最新点に値を表示"""
    if not data:
        print("グラフを作成するデータがありません。")
        return None
    
    df = pd.DataFrame(data)
    df = df.sort_values("date")
    
    fig, ax = plt.subplots(figsize=(16, 10))
    
    for zone_name in ZONE_SHORT_NAMES:
        col_name = f"{zone_name}_visitors"
        if col_name in df.columns:
            series = df[["date", col_name]].dropna()
            if series.empty:
                continue
            line, = ax.plot(series["date"], series[col_name], marker="o", label=zone_name, linewidth=2.5, markersize=8)
            # 最新点に値を表示
            last_row = series.iloc[-1]
            ts_str = last_row["date"].strftime("%Y/%m/%d %H:%M")
            ax.annotate(
                f"{int(last_row[col_name])}\n{ts_str}",
                xy=(last_row["date"], last_row[col_name]),
                xytext=(8, 0),
                textcoords="offset points",
                ha="left",
                va="center",
                fontsize=11,
                fontweight="bold",
                color=line.get_color(),
                bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor=line.get_color(), linewidth=0.8, alpha=0.85)
            )
    
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
    
    # イベント情報を重畳表示
    if events:
        add_events_to_graph(ax, events, y_min, y_max)
    
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


def create_zone_likes_graph(data, output_dir, events=None):
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
    
    # イベント情報を重畳表示
    if events:
        add_events_to_graph(ax, events, y_min, y_max)
    
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


def normalize_datetime_str(dt_str, filename=None):
    """日時文字列を正規化する（様々な形式に対応）"""
    if pd.isna(dt_str) or str(dt_str).strip() == "":
        # filenameから日時を抽出
        if filename and filename.startswith("IPTeCA_"):
            try:
                if filename.endswith("_JST.html"):
                    timestamp_str = filename.replace("IPTeCA_", "").replace("_JST.html", "")
                elif filename.endswith("_JST.png"):
                    timestamp_str = filename.replace("IPTeCA_", "").replace("_JST.png", "")
                else:
                    return None
                dt = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                return None
        return None
    
    dt_str = str(dt_str).strip()
    
    # スラッシュ区切りをハイフン区切りに変換
    dt_str = dt_str.replace("/", "-")
    
    # 時刻が不完全な場合（例: "2025-11-19 8:33"）を補完
    # "YYYY-MM-DD H:MM" 形式を "YYYY-MM-DD HH:MM:SS" に変換
    if re.match(r'^\d{4}-\d{2}-\d{2} \d{1,2}:\d{2}$', dt_str):
        # 秒を追加
        dt_str = dt_str + ":00"
    elif re.match(r'^\d{4}-\d{2}-\d{2} \d{1,2}:\d{2}:\d{2}$', dt_str):
        # 既に秒がある場合はそのまま
        pass
    elif re.match(r'^\d{4}-\d{2}-\d{2}$', dt_str):
        # 日付のみの場合は時刻を追加
        dt_str = dt_str + " 00:00:00"
    
    return dt_str


def load_from_csv(csv_path):
    """CSVファイルからHTML情報を読み込む（HTMLファイルと手動データの両方を含む）"""
    if not os.path.exists(csv_path):
        print(f"エラー: CSVファイルが見つかりません: {csv_path}")
        return None
    
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    jst = ZoneInfo("Asia/Tokyo")
    
    # 日時文字列を正規化
    for idx, row in df.iterrows():
        filename = row.get("filename", "")
        date_str = normalize_datetime_str(row.get("date_str"), filename)
        if date_str:
            df.at[idx, "date_str"] = date_str
        
        # file_date_strが空の場合は、date_strと同じ値を使用
        file_date_str = row.get("file_date_str")
        if pd.isna(file_date_str) or str(file_date_str).strip() == "":
            df.at[idx, "file_date_str"] = df.at[idx, "date_str"]
        else:
            file_date_str = normalize_datetime_str(file_date_str, filename)
            if file_date_str:
                df.at[idx, "file_date_str"] = file_date_str
    
    # 日時文字列をdatetimeオブジェクトに変換
    try:
        df["date"] = pd.to_datetime(df["date_str"], errors="coerce").dt.tz_localize(jst, ambiguous="infer")
    except Exception as e:
        print(f"警告: 日時の変換でエラーが発生しました: {e}")
        # フォールバック: ファイル名から日時を抽出
        for idx, row in df.iterrows():
            if pd.isna(df.at[idx, "date"]):
                filename = row.get("filename", "")
                if filename.startswith("IPTeCA_"):
                    try:
                        if filename.endswith("_JST.html"):
                            timestamp_str = filename.replace("IPTeCA_", "").replace("_JST.html", "")
                        elif filename.endswith("_JST.png"):
                            timestamp_str = filename.replace("IPTeCA_", "").replace("_JST.png", "")
                        else:
                            continue
                        dt = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                        df.at[idx, "date"] = dt.replace(tzinfo=jst)
                    except Exception:
                        pass
    
    try:
        df["file_date"] = pd.to_datetime(df["file_date_str"], errors="coerce").dt.tz_localize(jst, ambiguous="infer")
        # file_dateがNaNの場合は、dateと同じ値を使用
        df["file_date"] = df["file_date"].fillna(df["date"])
    except Exception as e:
        print(f"警告: file_dateの変換でエラーが発生しました: {e}")
        df["file_date"] = df["date"]
    
    # dateがNaNの行を除外
    df = df.dropna(subset=["date"])
    
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
                # NaNの場合は0に変換
                value = row.get(visitors_col, 0)
                row_data[visitors_col] = 0 if pd.isna(value) else float(value)
            if likes_col in df.columns:
                value = row.get(likes_col, 0)
                row_data[likes_col] = 0 if pd.isna(value) else float(value)
        
        data.append(row_data)
    
    return data


def analyze_html():
    """HTMLファイルを解析してグラフを作成"""
    html_dir = "html"
    output_dir = "graphs"
    csv_path = os.path.join(output_dir, "html_data.csv")
    
    # 日本語フォントを設定
    setup_japanese_font()
    
    # 既存のCSVファイルから全データを読み込む（手動データも含む）
    all_data = []
    if os.path.exists(csv_path):
        print(f"CSVファイルから全データを読み込みます: {csv_path}")
        data_from_csv = load_from_csv(csv_path)
        if data_from_csv:
            all_data.extend(data_from_csv)
            print(f"CSVから {len(data_from_csv)} 件のデータを読み込みました。")
    
    # HTMLファイルを取得
    print(f"htmlフォルダをスキャン中: {html_dir}")
    html_data = get_html_files(html_dir)
    
    if html_data:
        print(f"HTMLファイルを {len(html_data)} 件見つけました。")
        # HTMLデータをCSVに保存（追記形式、重複は上書き）
        save_to_csv(html_data, output_dir, csv_path)
        
        # 更新されたCSVから全データを再読み込み
        print(f"更新されたCSVファイルから全データを再読み込みます: {csv_path}")
        data_from_csv = load_from_csv(csv_path)
        if data_from_csv:
            all_data = data_from_csv
            print(f"CSVから {len(data_from_csv)} 件のデータを読み込みました。")
    elif not all_data:
        print(f"エラー: {html_dir} フォルダにHTMLファイルが見つからず、CSVファイルもありませんでした。")
        sys.exit(1)
    
    if not all_data:
        print("エラー: グラフを作成するデータがありません。")
        sys.exit(1)
    
    # 日時でソート
    all_data.sort(key=lambda x: x["date"])
    
    # イベント情報を読み込む
    events = load_events("events.json")
    if events:
        print(f"イベント情報を {len(events)} 件読み込みました。")
    
    # グラフを作成
    create_timeline_graph(all_data, output_dir)
    create_daily_count_graph(all_data, output_dir)
    create_hourly_distribution_graph(all_data, output_dir)
    
    # ゾーンデータのグラフを作成（イベント情報を重畳表示）
    create_zone_visitors_graph(all_data, output_dir, events=events)
    create_zone_likes_graph(all_data, output_dir, events=events)
    
    print(f"\nすべてのグラフとCSVを {output_dir}/ フォルダに保存しました。")


if __name__ == "__main__":
    try:
        analyze_html()
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

