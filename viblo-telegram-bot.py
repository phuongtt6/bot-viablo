"""Fetch newest Viblo posts and push unseen ones to Telegram."""

from __future__ import annotations

import html
import json
import os
import sys
import time
from pathlib import Path

import feedparser
import requests

VIBLO_RSS_URL = "https://viblo.asia/rss"
SENT_FILE = Path(__file__).parent / "sent.json"
MAX_POSTS_PER_RUN = int(os.environ.get("MAX_POSTS", "5"))
SENT_HISTORY_LIMIT = 500
TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def load_sent() -> list[str]:
    if not SENT_FILE.exists():
        return []
    try:
        data = json.loads(SENT_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def save_sent(ids: list[str]) -> None:
    trimmed = ids[-SENT_HISTORY_LIMIT:]
    SENT_FILE.write_text(
        json.dumps(trimmed, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def fetch_posts() -> list[dict]:
    headers = {"User-Agent": "Mozilla/5.0 (bot-viablo)"}
    response = requests.get(VIBLO_RSS_URL, headers=headers, timeout=30)
    response.raise_for_status()
    feed = feedparser.parse(response.content)
    return [
        {
            "id": entry.get("id") or entry.get("link"),
            "title": entry.get("title", "").strip(),
            "link": entry.get("link", "").strip(),
            "author": entry.get("author", "").strip() or "Unknown",
            "summary": entry.get("summary", "").strip(),
            "published": entry.get("published", ""),
        }
        for entry in feed.entries
        if entry.get("link")
    ]


def escape_html(text: str) -> str:
    # RSS may contain entities like &quot;; decode then re-escape for Telegram HTML.
    return html.escape(html.unescape(text), quote=False)


def format_message(post: dict) -> str:
    title = escape_html(post["title"])
    author = escape_html(post["author"])
    link = post["link"]
    summary = escape_html(post["summary"])[:300]
    if len(post["summary"]) > 300:
        summary += "..."
    return (
        f"<b><a href=\"{link}\">{title}</a></b>\n"
        f"By: {author}\n\n"
        f"{summary}\n\n"
        f"<a href=\"{link}\">Read on Viblo →</a>"
    )


def send_to_telegram(token: str, chat_id: str, text: str) -> None:
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    url = TELEGRAM_API.format(token=token)
    response = requests.post(url, json=payload, timeout=30)
    if not response.ok:
        raise RuntimeError(
            f"Telegram error {response.status_code}: {response.text}"
        )


def main() -> int:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("ERROR: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID required", file=sys.stderr)
        return 1

    sent_ids = load_sent()
    sent_set = set(sent_ids)

    posts = fetch_posts()
    if not posts:
        print("No posts found in feed")
        return 0

    new_posts = [p for p in posts if p["id"] not in sent_set][:MAX_POSTS_PER_RUN]
    if not new_posts:
        print("No new posts since last run")
        return 0

    # Send oldest first so newest appears at the bottom of the chat.
    for post in reversed(new_posts):
        try:
            send_to_telegram(token, chat_id, format_message(post))
            sent_ids.append(post["id"])
            print(f"Sent: {post['title']}")
            time.sleep(1)  # Telegram rate-limit cushion
        except Exception as exc:  # noqa: BLE001
            print(f"Failed to send '{post['title']}': {exc}", file=sys.stderr)

    save_sent(sent_ids)
    print(f"Done. {len(new_posts)} new post(s) sent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
