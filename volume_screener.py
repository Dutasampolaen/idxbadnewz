#!/usr/bin/env python3
"""
Indonesian Stock Volume Screener
Detects 3x volume spikes and special watchlist patterns.
Runs Mon-Fri at 16:20 WIB (09:20 UTC).
"""

import os
import json
import yfinance as yf
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import pytz

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
MAX_TICKERS_PER_RUN = int(os.getenv("MAX_TICKERS_PER_RUN", "120"))

WATCHLIST_FILE = Path("/opt/indo_badnews/watchlist.json")
IHSG_FILE = Path("/opt/indo_badnews/ihsg_tickers.txt")
SCREENER_FILE = Path("/opt/indo_badnews/screener_tickers.txt")

WIB = pytz.timezone("Asia/Jakarta")


def log(msg):
    """Print with WIB timestamp"""
    now_wib = datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S %Z")
    print(f"[{now_wib}] {msg}")


def send_telegram(text):
    """Send message to Telegram"""
    import requests

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


def load_ticker_file(filepath):
    """Load tickers from a file"""
    if not filepath.exists():
        return []

    tickers = []
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                tickers.append(line)
    return tickers


def get_ticker_universe():
    """Build ticker universe: watchlist + IHSG + screener file"""
    tickers = set()

    watchlist = load_watchlist()
    tickers.update(watchlist)
    log(f"✓ Watchlist: {len(watchlist)} tickers")

    ihsg = load_ticker_file(IHSG_FILE)
    tickers.update(ihsg)
    log(f"✓ IHSG file: {len(ihsg)} tickers")

    screener = load_ticker_file(SCREENER_FILE)
    tickers.update(screener)
    log(f"✓ Screener file: {len(screener)} tickers")

    return list(tickers), set(watchlist)


def get_ohlcv_data(ticker, period="1mo"):
    """Fetch OHLCV data from Yahoo Finance"""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)

        if df.empty:
            return None

        df = df.reset_index()
        return df

    except Exception as e:
        log(f"❌ Failed to fetch {ticker}: {e}")
        return None


def detect_volume_spike(df):
    """
    Detect 3x volume spike with classification.
    Returns: (spike_date, spike_volume, avg_volume, close_price, prev_close, classification)
    """
    if len(df) < 21:
        return None

    recent = df.tail(21).copy()
    recent = recent.reset_index(drop=True)

    for i in range(len(recent) - 1, 0, -1):
        current_row = recent.iloc[i]
        prev_row = recent.iloc[i - 1]

        current_volume = current_row["Volume"]
        prev_close = prev_row["Close"]
        current_close = current_row["Close"]

        past_20 = recent.iloc[max(0, i - 20):i]
        if len(past_20) < 5:
            continue

        avg_volume = past_20["Volume"].mean()

        if current_volume >= 3 * avg_volume and current_close >= prev_close * 1.02:
            future_candles = recent.iloc[i + 1:]

            if len(future_candles) == 0:
                classification = "WAIT"
            else:
                future_5 = future_candles.head(5)

                if len(future_5) < 3:
                    classification = "WAIT"
                else:
                    high_volume_count = (future_5["Volume"] > current_volume * 0.6).sum()

                    if high_volume_count > 0:
                        classification = "WAIT"
                    else:
                        classification = "SETUP"

            return {
                "date": current_row["Date"].strftime("%Y-%m-%d"),
                "spike_volume": current_volume,
                "avg_volume": avg_volume,
                "close": current_close,
                "prev_close": prev_close,
                "classification": classification
            }

    return None


def detect_watchlist_patterns(df):
    """
    Detect special watchlist patterns:
    - Price up ≥1%, volume down ≥30%
    - Price down ≥1%, volume up ≥30%
    """
    if len(df) < 2:
        return []

    patterns = []
    recent = df.tail(10)

    for i in range(1, len(recent)):
        current = recent.iloc[i]
        prev = recent.iloc[i - 1]

        price_change = ((current["Close"] - prev["Close"]) / prev["Close"]) * 100
        volume_change = ((current["Volume"] - prev["Volume"]) / prev["Volume"]) * 100

        if price_change >= 1 and volume_change <= -30:
            patterns.append({
                "date": current["Date"].strftime("%Y-%m-%d"),
                "type": "Price↑ Volume↓",
                "price_change": price_change,
                "volume_change": volume_change,
                "close": current["Close"]
            })

        elif price_change <= -1 and volume_change >= 30:
            patterns.append({
                "date": current["Date"].strftime("%Y-%m-%d"),
                "type": "Price↓ Volume↑",
                "price_change": price_change,
                "volume_change": volume_change,
                "close": current["Close"]
            })

    return patterns[-3:]


def main():
    log("=== Indonesian Volume Screener ===")

    tickers, watchlist_set = get_ticker_universe()

    if len(tickers) > MAX_TICKERS_PER_RUN:
        log(f"⚠️  Limiting to {MAX_TICKERS_PER_RUN} tickers (from {len(tickers)})")
        tickers = tickers[:MAX_TICKERS_PER_RUN]

    log(f"✓ Total tickers to screen: {len(tickers)}")

    spikes_setup = []
    spikes_wait = []
    watchlist_patterns = []

    for idx, ticker in enumerate(tickers, 1):
        if idx % 20 == 0:
            log(f"⏳ Processing {idx}/{len(tickers)}...")

        df = get_ohlcv_data(ticker)
        if df is None:
            continue

        spike = detect_volume_spike(df)
        if spike:
            spike["ticker"] = ticker

            if spike["classification"] == "SETUP":
                spikes_setup.append(spike)
                log(f"🚀 SETUP: {ticker}")
            else:
                spikes_wait.append(spike)

        if ticker in watchlist_set:
            patterns = detect_watchlist_patterns(df)
            for pattern in patterns:
                pattern["ticker"] = ticker
                watchlist_patterns.append(pattern)
                log(f"⚠️  Pattern: {ticker} - {pattern['type']}")

    log("✓ Screening complete")

    log(f"📊 SETUP spikes: {len(spikes_setup)}")
    log(f"⏳ WAIT spikes: {len(spikes_wait)}")
    log(f"⚠️  Watchlist patterns: {len(watchlist_patterns)}")

    messages = []

    if spikes_setup:
        msg = "🚀 <b>Volume SETUP Signals</b>\n\n"
        for spike in spikes_setup[:10]:
            ticker_clean = spike["ticker"].replace(".JK", "")
            price_change = ((spike["close"] - spike["prev_close"]) / spike["prev_close"]) * 100
            volume_ratio = spike["spike_volume"] / spike["avg_volume"]

            msg += f"<b>{ticker_clean}</b>\n"
            msg += f"📅 {spike['date']}\n"
            msg += f"💰 Rp {spike['close']:,.0f} (+{price_change:.1f}%)\n"
            msg += f"📊 Volume: {volume_ratio:.1f}x avg\n\n"

        if len(spikes_setup) > 10:
            msg += f"... and {len(spikes_setup) - 10} more\n"

        messages.append(msg)

    if watchlist_patterns:
        msg = "⚠️ <b>Watchlist Pattern Alerts</b>\n\n"
        for pattern in watchlist_patterns[:10]:
            ticker_clean = pattern["ticker"].replace(".JK", "")

            msg += f"<b>{ticker_clean}</b> - {pattern['type']}\n"
            msg += f"📅 {pattern['date']}\n"
            msg += f"💰 Rp {pattern['close']:,.0f}\n"
            msg += f"📈 Price: {pattern['price_change']:+.1f}%\n"
            msg += f"📊 Volume: {pattern['volume_change']:+.1f}%\n\n"

        if len(watchlist_patterns) > 10:
            msg += f"... and {len(watchlist_patterns) - 10} more\n"

        messages.append(msg)

    if messages:
        now_wib = datetime.now(WIB).strftime("%H:%M WIB")
        header = f"📊 <b>Volume Screener Report</b>\n⏰ {now_wib}\n\n"

        for message in messages:
            full_message = header + message
            send_telegram(full_message)

        log(f"✓ Sent {len(messages)} report(s)")
    else:
        log("✓ No signals to report")

    log("=== Screener Complete ===")


if __name__ == "__main__":
    main()
