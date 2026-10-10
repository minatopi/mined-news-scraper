import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


# ========================================
# 設定
# ========================================

BASE_URL = "https://mined.jp/"
OUTPUT_FILE = Path(__file__).resolve().parent / "mined_news.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; MinedNewsLearningBot/1.0)"
    )
}

TIMEOUT = 30


# ========================================
# Webページを取得
# ========================================

def fetch_html(url: str) -> str:
    """WebページのHTMLを取得する。"""
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    response.raise_for_status()

    # 日本語ページの文字コードを処理
    response.encoding = response.apparent_encoding

    return response.text


# ========================================
# ニュース一覧を解析
# ========================================

def scrape_news(html: str) -> list[dict]:
    """HTMLからニュース情報を抽出する。"""
    soup = BeautifulSoup(html, "html.parser")

    # ニュース一覧の親要素
    container = soup.select_one(
        'div[aria-label="news_scroll"]'
    )

    if container is None:
        raise ValueError(
            'ニュース一覧が見つかりません。'
            'HTMLに aria-label="news_scroll" があるか確認してください。'
        )

    # 各ニュースはaタグ
    items = container.select(":scope > a")

    if not items:
        raise ValueError(
            "ニュース項目が見つかりません。"
            "取得したHTMLの構造を確認してください。"
        )

    results = []

    for item in items:
        paragraphs = item.select("p")

        # 日付・カテゴリ・本文の3項目が必要
        if len(paragraphs) < 3:
            print(
                "警告: pタグが3個未満の項目をスキップしました。",
                file=sys.stderr,
            )
            continue

        date = paragraphs[0].get_text(
            " ", strip=True
        )
        category = paragraphs[1].get_text(
            " ", strip=True
        )
        description = paragraphs[2].get_text(
            " ", strip=True
        )

        # リンク先を取得
        href = item.get("href")

        if not href:
            print(
                f"警告: URLがない項目をスキップしました: {description}",
                file=sys.stderr,
            )
            continue

        link = urljoin(BASE_URL, href)

        results.append({
            "date": date,
            "category": category,
            "description": description,
            "url": link,
        })

    if not results:
        raise ValueError(
            "ニュース情報を抽出できませんでした。"
        )

    return results


# ========================================
# JSONファイルに保存
# ========================================

def save_json(news: list[dict], output_file: Path) -> None:
    """ニュース一覧をUTF-8のJSONファイルに保存する。"""
    with output_file.open("w", encoding="utf-8") as file:
        json.dump(
            news,
            file,
            ensure_ascii=False,
            indent=2,
        )
        file.write("\n")


# ========================================
# メイン処理
# ========================================

def main() -> None:
    print(f"取得先: {BASE_URL}")

    try:
        html = fetch_html(BASE_URL)
        print("HTMLの取得に成功しました。")

        news = scrape_news(html)
        print(f"ニュースを {len(news)} 件取得しました。")

        save_json(news, OUTPUT_FILE)

        print(f"保存先: {OUTPUT_FILE}")
        print("スクレイピングが完了しました。")

        # 取得結果の一部を表示
        print("\n--- 取得結果のサンプル ---")

        for item in news[:3]:
            print(json.dumps(
                item,
                ensure_ascii=False,
                indent=2,
            ))

    except requests.RequestException as error:
        print(
            f"HTTPリクエストに失敗しました: {error}",
            file=sys.stderr,
        )
        sys.exit(1)

    except (ValueError, OSError) as error:
        print(
            f"処理に失敗しました: {error}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
