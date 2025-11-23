#!/usr/bin/env python3
"""
Indonesian Stock Bad News Scanner
Runs every 10 minutes via systemd timer, but only executes during WIB trading slots.
"""

import os
import sys
import json
import requests
import feedparser
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import pytz
import hashlib
import time

# Load environment
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
MARKETAUX_API_KEY = os.getenv("MARKETAUX_API_KEY")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
MAX_NEWS_AGE_DAYS = int(os.getenv("MAX_NEWS_AGE_DAYS", "3"))

STATE_FILE = Path("/opt/indo_badnews/state.json")
WATCHLIST_FILE = Path("/opt/indo_badnews/watchlist.json")

WIB = pytz.timezone("Asia/Jakarta")

TRADING_SLOTS = [
    {"start": (8, 45), "end": (9, 30), "name": "Pre-Market"},
    {"start": (12, 0), "end": (13, 30), "name": "Midday"},
    {"start": (15, 15), "end": (16, 0), "name": "Post-Market"}
]

NEGATIVE_KEYWORDS = [
    "kerugian", "merugi", "turun", "anjlok", "korupsi", "skandal",
    "penipuan", "bangkrut", "gagal", "ditangkap", "tersangka", "tuntutan",
    "denda", "pailit", "resesi", "krisis", "collapse", "fraud", "lawsuit",
    "bankruptcy", "scandal", "arrest", "corruption", "loss", "plunge", "drop"
]


def log(msg):
    """Print with WIB timestamp"""
    now_wib = datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S %Z")
    print(f"[{now_wib}] {msg}")


def get_current_slot():
    """Check if current time is within a trading slot"""
    now_wib = datetime.now(WIB)
    current_time = (now_wib.hour, now_wib.minute)

    for idx, slot in enumerate(TRADING_SLOTS):
        start_h, start_m = slot["start"]
        end_h, end_m = slot["end"]

        if (start_h, start_m) <= current_time <= (end_h, end_m):
            slot_id = f"{now_wib.strftime('%Y-%m-%d')}_slot_{idx}"
            return slot_id, slot["name"]

    return None, None


def load_state():
    """Load seen articles and last slot"""
    if STATE_FILE.exists():
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"seen": [], "last_slot": None}


def save_state(state):
    """Save state to disk"""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def load_watchlist():
    """Load all tickers from all chats"""
    if WATCHLIST_FILE.exists():
        with open(WATCHLIST_FILE, "r") as f:
            data = json.load(f)
            tickers = set()
            for chat_id, chat_tickers in data.items():
                tickers.update(chat_tickers)
            return list(tickers)
    return []


def send_telegram(text):
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log("⚠️  Telegram not configured, skipping send")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except Exception as e:
        log(f"❌ Telegram send failed: {e}")


def fetch_marketaux_news():
    """Fetch news from Marketaux API"""
    if not MARKETAUX_API_KEY:
        log("⚠️  Marketaux API key not configured")
        return []

    url = "https://api.marketaux.com/v1/news/all"
    params = {
        "api_token": MARKETAUX_API_KEY,
        "countries": "id",
        "filter_entities": "true",
        "language": "id,en",
        "limit": 50
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        articles = []
        for item in data.get("data", []):
            articles.append({
                "id": item.get("uuid", hashlib.md5(item.get("url", "").encode()).hexdigest()),
                "title": item.get("title", ""),
                "description": item.get("description", ""),
                "url": item.get("url", ""),
                "published": item.get("published_at", ""),
                "source": "Marketaux"
            })

        log(f"✓ Fetched {len(articles)} articles from Marketaux")
        return articles

    except Exception as e:
        log(f"❌ Marketaux fetch failed: {e}")
        return []


def fetch_rss_feed(url, source_name):
    """Fetch articles from RSS feed"""
    try:
        feed = feedparser.parse(url)
        articles = []

        for entry in feed.entries[:50]:
            article_id = entry.get("id") or entry.get("link") or entry.get("title", "")
            article_id = hashlib.md5(article_id.encode()).hexdigest()

            published = entry.get("published", entry.get("updated", ""))

            articles.append({
                "id": article_id,
                "title": entry.get("title", ""),
                "description": entry.get("summary", entry.get("description", "")),
                "url": entry.get("link", ""),
                "published": published,
                "source": source_name
            })

        log(f"✓ Fetched {len(articles)} articles from {source_name}")
        return articles

    except Exception as e:
        log(f"❌ RSS fetch failed for {source_name}: {e}")
        return []


def fetch_google_news_rss(query):
    """Fetch Google News RSS for a specific query"""
    url = f"https://news.google.com/rss/search?q={query}&hl=id&gl=ID&ceid=ID:id"
    return fetch_rss_feed(url, f"Google News ({query})")


def is_article_recent(published_str):
    """Check if article is within MAX_NEWS_AGE_DAYS"""
    if not published_str:
        return True

    try:
        from dateutil import parser
        published_dt = parser.parse(published_str)
        cutoff = datetime.now(pytz.UTC) - timedelta(days=MAX_NEWS_AGE_DAYS)
        return published_dt > cutoff
    except:
        return True


def has_negative_keywords(text):
    """Check if text contains negative keywords"""
    text_lower = text.lower()
    for keyword in NEGATIVE_KEYWORDS:
        if keyword in text_lower:
            return True
    return False


def classify_with_ai(title, description):
    """Use local Ollama AI to classify article as BAD or OK"""
    prompt = f"""Classify this Indonesian stock news article as BAD or OK.
BAD = negative impact on stock (fraud, loss, bankruptcy, corruption, lawsuit, collapse, scandal, arrest)
OK = neutral or positive

Article: {title}
{description}

Respond with ONLY "BAD" or "OK":"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 10
        }
    }

    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        answer = result.get("response", "").strip().upper()

        if "BAD" in answer:
            return "BAD"
        elif "OK" in answer:
            return "OK"
        else:
            log(f"⚠️  AI returned unclear response: {answer}")
            return "OK"

    except Exception as e:
        log(f"❌ AI classification failed: {e}")
        return "OK"


def classify_article(article):
    """Classify article as BAD or OK"""
    text = f"{article['title']} {article['description']}"

    if has_negative_keywords(text):
        return "BAD"

    return classify_with_ai(article['title'], article['description'])


def main():
    log("=== Indonesian Bad News Scanner ===")

    force_run = os.getenv("FORCE_RUN") == "1"

    if not force_run:
        slot_id, slot_name = get_current_slot()

        if not slot_id:
            log("⏸️  Outside trading slots, exiting")
            sys.exit(0)

        state = load_state()

        if state.get("last_slot") == slot_id:
            log(f"✓ Already ran for {slot_name} slot today, exiting")
            sys.exit(0)

        log(f"✓ Running for {slot_name} slot (ID: {slot_id})")
    else:
        log("⚡ FORCE_RUN mode enabled")
        slot_id = f"force_{int(time.time())}"
        slot_name = "Manual"
        state = load_state()

    watchlist_tickers = load_watchlist()
    log(f"✓ Watchlist: {len(watchlist_tickers)} tickers")

    all_articles = []

    all_articles.extend(fetch_marketaux_news())
    all_articles.extend(fetch_rss_feed(
        "https://news.google.com/rss/search?q=saham+indonesia&hl=id&gl=ID&ceid=ID:id",
        "Google News"
    ))
    all_articles.extend(fetch_rss_feed(
        "https://www.cnbcindonesia.com/market/rss",
        "CNBC Indonesia"
    ))

    for ticker in watchlist_tickers[:10]:
        ticker_clean = ticker.replace(".JK", "")
        all_articles.extend(fetch_google_news_rss(f"{ticker_clean} saham"))

    log(f"✓ Total articles fetched: {len(all_articles)}")

    seen_ids = set(state.get("seen", []))
    new_articles = []

    for article in all_articles:
        if article["id"] not in seen_ids and is_article_recent(article["published"]):
            new_articles.append(article)
            seen_ids.add(article["id"])

    log(f"✓ New unseen articles: {len(new_articles)}")

    bad_articles = []
    for article in new_articles:
        classification = classify_article(article)
        if classification == "BAD":
            bad_articles.append(article)
            log(f"🚨 BAD: {article['title'][:60]}...")

    log(f"✓ Bad news articles: {len(bad_articles)}")

    max_send = 5
    articles_to_send = bad_articles[:max_send]

    if articles_to_send:
        now_wib = datetime.now(WIB).strftime("%H:%M WIB")
        header = f"🚨 <b>Bad News Alert - {slot_name}</b>\n⏰ {now_wib}\n\n"

        messages = []
        for idx, article in enumerate(articles_to_send, 1):
            msg = f"{idx}. <b>{article['title']}</b>\n"
            if article['description']:
                desc = article['description'][:200]
                msg += f"{desc}...\n"
            msg += f"🔗 {article['url']}\n"
            msg += f"📰 {article['source']}\n"
            messages.append(msg)

        full_message = header + "\n".join(messages)

        if len(bad_articles) > max_send:
            full_message += f"\n\n... and {len(bad_articles) - max_send} more bad news articles"

        send_telegram(full_message)
        log(f"✓ Sent {len(articles_to_send)} bad news alerts")
    else:
        log("✓ No bad news to report")

    state["seen"] = list(seen_ids)[-1000:]
    state["last_slot"] = slot_id
    save_state(state)

    log("✓ State saved")
    log("=== Scanner Complete ===")


if __name__ == "__main__":
    main()
