"""
Foreign Policy Blogs RSS Parser
抓取 foreignpolicyblogs.com/feed/ 全文 RSS，按日期保存为 Markdown。
去重机制：processed_urls.json 持久化已处理链接。
"""
import feedparser
import html2text
import os
import json
from datetime import datetime, timezone, timedelta
import pytz

RSS_URL = "https://foreignpolicyblogs.com/feed/"
OUTPUT_DIR = "dailynews"
PROCESSED_FILE = "processed_urls.json"
MAX_DAILY = 20
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


def fetch_rss(force_backfill=False):
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

    if not force_backfill:
        candidates = []
        for entry in feed.entries:
            link = entry.get("link", "")
            if not link or link in processed:
                continue
            pub_dt = None
            try:
                pub_struct = entry.get("published_parsed")
                if pub_struct:
                    pub_dt = datetime(*pub_struct[:6], tzinfo=timezone.utc)
            except Exception:
                pass
            if pub_dt:
                us_dt = pub_dt.astimezone(TZ_US)
                if us_dt.strftime("%Y-%m-%d") != today_str:
                    continue
            else:
                continue
            candidates.append(entry)

        print(f"Today ({today_str}) new articles: {len(candidates)}")
        if not candidates:
            print("No new articles today, skip")
            return []
        selected = candidates[:MAX_DAILY]
    else:
        backfill_days = int(os.getenv("BACKFILL_DAYS", "7"))
        print(f"Backfill mode: last {backfill_days} days")
        cutoff = now_us - timedelta(days=backfill_days)
        candidates = []
        for entry in feed.entries:
            link = entry.get("link", "")
            if not link:
                continue
            pub_dt = None
            try:
                pub_struct = entry.get("published_parsed")
                if pub_struct:
                    pub_dt = datetime(*pub_struct[:6], tzinfo=timezone.utc)
            except Exception:
                pass
            if pub_dt:
                us_dt = pub_dt.astimezone(TZ_US)
                if us_dt < cutoff:
                    continue
            candidates.append(entry)
        selected = [e for e in candidates
                    if e.get("link", "") not in processed
                    or not processed[e.get("link", "")].get("sent")]
        selected = selected[:MAX_DAILY]

    print(f"Selected {len(selected)} articles")

    h = html2text.HTML2Text()
    h.body_width = 0
    h.ignore_links = False
    h.ignore_images = True

    saved = []
    for entry in selected:
        title = entry.get("title", "No Title")
        link = entry.get("link", "")
        author = entry.get("author", "")

        # 优先取 content:encoded（全文），其次 summary
        content_html = ""
        if hasattr(entry, "content") and entry.content:
            content_html = entry.content[0].get("value", "")
        if not content_html and hasattr(entry, "summary"):
            content_html = entry.summary or ""

        content_md = h.handle(content_html).strip() if content_html else "(No content)"

        pub_str = today_str
        try:
            pub_struct = entry.get("published_parsed")
            if pub_struct:
                pub_dt = datetime(*pub_struct[:6], tzinfo=timezone.utc)
                pub_str = pub_dt.astimezone(TZ_US).strftime("%Y-%m-%d")
        except Exception:
            pass

        author_line = f"作者：{author}\n\n" if author else ""
        item = f"## {title}\n\n链接：{link}\n\n{author_line}{content_md}\n\n---\n\n"

        mode = "a" if os.path.exists(today_file) else "w"
        with open(today_file, mode, encoding="utf-8") as f:
            f.write(item)

        processed[link] = {"title": title, "sent": False, "date": pub_str}
        saved.append(link)
        print(f"  Saved: {title[:70]}")

    save_processed(processed)
    print(f"Added {len(saved)} articles -> {today_file}")
    return saved


def mark_sent(urls):
    processed = load_processed()
    for url in urls:
        if url in processed:
            processed[url]["sent"] = True
    save_processed(processed)


if __name__ == "__main__":
    mode = os.getenv("MODE", "normal")
    fetch_rss(force_backfill=(mode == "backfill"))
