"""
Foreign Policy Blogs RSS Parser
每次最多抓取3篇新文章，已处理的不再重复。
"""
import feedparser
import html2text
import os
import json
import re
from datetime import datetime, timezone
import pytz

RSS_URL = "https://foreignpolicyblogs.com/feed/"
OUTPUT_DIR = "dailynews"
PROCESSED_FILE = "processed_urls.json"
MAX_ARTICLES = 3  # 每次最多抓取文章数

TZ_US = pytz.timezone("America/New_York")


def load_processed():
    if os.path.exists(PROCESSED_FILE):
        try:
            with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_processed(data):
    with open(PROCESSED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def fetch_rss():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    processed = load_processed()

    print(f"Fetching: {RSS_URL}")
    feed = feedparser.parse(RSS_URL)
    if not feed.entries:
        print("WARNING: RSS entries empty")
        return []

    now_us = datetime.now(TZ_US)
    today_str = now_us.strftime("%Y-%m-%d")
    today_file = os.path.join(OUTPUT_DIR, today_str + ".md")

    candidates = []
    for entry in feed.entries:
        link = entry.get("link", "")
        if not link:
            continue
        if link in processed:
            print(f"  Skip (already processed): {link[:60]}...")
            continue
        candidates.append(entry)

    print(f"Found {len(candidates)} new articles, selecting {MAX_ARTICLES}")
    selected = candidates[:MAX_ARTICLES]

    if not selected:
        print("No new articles to process")
        return []

    h = html2text.HTML2Text()
    h.body_width = 0
    h.ignore_links = False
    h.ignore_images = True

    saved_links = []
    for entry in selected:
        title = entry.get("title", "No Title")
        link = entry.get("link", "")
        author = entry.get("author", "")

        # 获取全文：优先 content:encoded，其次 summary
        content_html = ""
        if hasattr(entry, "content") and entry.content:
            content_html = entry.content[0].get("value", "")
        if not content_html and hasattr(entry, "summary"):
            content_html = entry.summary or ""

        content_md = h.handle(content_html).strip() if content_html else "(No content)"

        author_line = f"作者：{author}\n\n" if author else ""
        item = f"## {title}\n\n链接：{link}\n\n{author_line}{content_md}\n\n---\n\n"

        mode = "a" if os.path.exists(today_file) else "w"
        with open(today_file, mode, encoding="utf-8") as f:
            f.write(item)

        processed[link] = {"title": title, "processed": True, "date": today_str}
        saved_links.append(link)
        print(f"  Saved: {title[:60]}...")

    save_processed(processed)
    print(f"Added {len(saved_links)} articles -> {today_file}")
    return saved_links


if __name__ == "__main__":
    fetch_rss()