import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

URL = "https://mined.jp/"

headers = {
    "User-Agent": "Mozilla/5.0 (compatible; MinedNewsLearningBot/1.0)"
}

# 1. Webページを取得
response = requests.get(URL, headers=headers, timeout=30)
response.raise_for_status()
response.encoding = response.apparent_encoding

# 2. HTMLを解析
soup = BeautifulSoup(response.text, "html.parser")

# 3. ニュース一覧を取得
news_list = soup.select(
    'div[aria-label="news_scroll"] > a'
)

results = []

for item in news_list:
    # 各ニュース内のpタグを取得
    paragraphs = item.select("p")

    # 日付・カテゴリ・本文がそろっているか確認
    if len(paragraphs) < 3:
        continue

    date = paragraphs[0].get_text(" ", strip=True)
    category = paragraphs[1].get_text(" ", strip=True)
    description = paragraphs[2].get_text(" ", strip=True)

    # リンクを取得（相対URLにも対応）
    link = urljoin(URL, item.get("href", ""))

    results.append({
        "date": date,
        "category": category,
        "description": description,
        "url": link,
    })

with open(
    "mined_news.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        results,
        f,
        ensure_ascii=False,
        indent=2
    )

print(f"{len(results)}件のニュースを取得しました。")
print("mined_news.json に保存しました。")
