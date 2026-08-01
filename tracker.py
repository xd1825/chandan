"""
YouTube Management Interview Tracker
-------------------------------------
Runs once a day (via GitHub Actions cron). For each company in watchlist.csv,
searches YouTube for videos uploaded in the last 24h, filters to genuine
management interviews (CEO/MD/CFO interviews, earnings calls, analyst/investor
meets), excludes stock-analysis/price-target content, dedupes against
previously-seen videos, and sends a Telegram alert for anything new.

Env vars required (set as GitHub Actions secrets):
  YOUTUBE_API_KEY
  TELEGRAM_BOT_TOKEN
  TELEGRAM_CHAT_ID
"""

import csv
import json
import os
import sys
from datetime import datetime, timedelta, timezone

import requests

WATCHLIST_FILE = "watchlist.csv"
SEEN_FILE = "seen_videos.json"
LOOKBACK_HOURS = 24

# Words that signal a genuine management interview / official corporate content
INCLUDE_KEYWORDS = [
    "interview", "md interview", "ceo interview", "cfo interview", "cmd interview",
    "concall", "conference call", "earnings call", "analyst meet", "analyst call",
    "investor meet", "investor conference", "in conversation with", "exclusive interview",
    "management interview", "q&a with", "chairman interview", "managing director",
]

# Words that signal third-party commentary / analysis / trading content — hard exclude
EXCLUDE_KEYWORDS = [
    "target price", "buy or sell", "should you buy", "technical analysis",
    "chart pattern", "price prediction", "stock to buy", "multibagger",
    "share price target", "trading strategy", "intraday", "swing trade",
    "breakout", "support resistance", "portfolio review",
]

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


def load_watchlist():
    with open(WATCHLIST_FILE, newline="", encoding="utf-8") as f:
        return [row for row in csv.DictReader(f)]


def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_seen(seen_ids):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(seen_ids), f, indent=2)


def is_genuine_interview(title, description):
    text = f"{title} {description}".lower()
    if any(bad in text for bad in EXCLUDE_KEYWORDS):
        return False
    return any(good in text for good in INCLUDE_KEYWORDS)


def search_youtube(api_key, query, published_after):
    params = {
        "key": api_key,
        "part": "snippet",
        "q": query,
        "type": "video",
        "order": "date",
        "publishedAfter": published_after,
        "maxResults": 15,
        "relevanceLanguage": "en",
    }
    resp = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get("items", [])


def send_telegram(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    resp = requests.post(
        url,
        data={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": "false",
        },
        timeout=30,
    )
    resp.raise_for_status()


def main():
    api_key = os.environ["YOUTUBE_API_KEY"]
    bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    watchlist = load_watchlist()
    seen_ids = load_seen()
    published_after = (
        datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    new_hits = []

    for row in watchlist:
        company = row["company"].strip()
        query = row["search_query"].strip()
        try:
            items = search_youtube(api_key, query, published_after)
        except requests.HTTPError as e:
            print(f"[WARN] YouTube search failed for {company}: {e}", file=sys.stderr)
            continue

        for item in items:
            video_id = item["id"]["videoId"]
            if video_id in seen_ids:
                continue
            snippet = item["snippet"]
            title = snippet["title"]
            description = snippet.get("description", "")
            channel = snippet["channelTitle"]

            seen_ids.add(video_id)  # mark seen regardless, so we never re-check it

            if is_genuine_interview(title, description):
                new_hits.append(
                    {
                        "company": company,
                        "title": title,
                        "channel": channel,
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                    }
                )

    if new_hits:
        lines = ["<b>New management interviews found:</b>", ""]
        for hit in new_hits:
            lines.append(f"<b>{hit['company']}</b> — {hit['title']}")
            lines.append(f"({hit['channel']})")
            lines.append(hit["url"])
            lines.append("")
        send_telegram(bot_token, chat_id, "\n".join(lines))
        print(f"Sent alert for {len(new_hits)} new interview(s).")
    else:
        print("No new interviews found. No alert sent.")

    save_seen(seen_ids)


if __name__ == "__main__":
    main()
