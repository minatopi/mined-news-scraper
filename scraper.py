import json
import sys
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


# ========================================
# 設定
# ========================================

BASE_URL = "https://mined.jp/"
OUTPUT_FILE = Path(__file__).resolve().parent / "mined_news.json"

# ページ読み込み後の待機時間（ミリ秒）
WAIT_AFTER_LOAD_MS = 5000

TIMEOUT_MS = 30000


# ========================================
# ニュース一覧を解析
# ========================================

def scrape_news(html: str) -> list[dict]:
    """HTMLからニュース情報を抽出する。"""
    soup = BeautifulSoup(html, "html.parser")

    container = soup.select_one(
        'div[aria-label="news_scroll"]'
    )

    if container is None:
        raise ValueError(
            'ニュース一覧が見つかりません。'
            'JavaScriptによる描画やHTML構造を確認してください。'
        )

    items = container.select(":scope > a")

    if not items:
        raise ValueError("ニュース項目が見つかりません。")

    results = []

    for item in items:
        paragraphs = item.select("p")

        if len(paragraphs) < 3:
            continue

        date = paragraphs[0].get_text(" ", strip=True)
        category = paragraphs[1].get_text(" ", strip=True)
        description = paragraphs[2].get_text(" ", strip=True)

        href = item.get("href")

        if not href:
            continue

        results.append({
            "date": date,
            "category": category,
            "description": description,
            "url": urljoin(BASE_URL, href),
        })

    if not results:
        raise ValueError("ニュース情報を抽出できませんでした。")

    return results


# ========================================
# JSONに保存
# ========================================

def save_json(news: list[dict]) -> None:
    """ニュースをJSONファイルに保存する。"""
    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
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
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)

            try:
                page = browser.new_page(
                    locale="ja-JP"
                )

                print(f"サイトを開いています: {BASE_URL}")

                page.goto(
                    BASE_URL,
                    wait_until="domcontentloaded",
                    timeout=TIMEOUT_MS,
                )

                print("ページを読み込みました。")
                print("5秒間待機しています...")

                # アニメーション・JavaScriptの描画を待つ
                page.wait_for_timeout(WAIT_AFTER_LOAD_MS)

                # 描画後のHTMLを取得
                html = page.content()

                print("HTMLを取得しました。")

                news = scrape_news(html)
                save_json(news)

                print(f"取得件数: {len(news)}件")
                print(f"JSON保存先: {OUTPUT_FILE}")
                print("スクレイピング完了！")

            finally:
                browser.close()

    except PlaywrightTimeoutError as error:
        print(
            f"ページ読み込みがタイムアウトしました: {error}",
            file=sys.stderr,
        )
        sys.exit(1)

    except Exception as error:
        print(f"エラーが発生しました: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
