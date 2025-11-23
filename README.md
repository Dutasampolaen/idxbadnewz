# Indonesian Stock Monitoring Stack

A comprehensive self-hosted monitoring system for Indonesian stocks with bad news detection, volume spike screening, and Telegram bot integration.

## Features

- **Telegram Watchlist Bot**: Add/remove tickers via Telegram commands
- **Bad News Scanner**: Multi-source news aggregation with AI classification
- **Volume Screener**: Detect 3x volume spikes with SETUP/WAIT classification
- **Automated Scheduling**: Systemd timers for hands-free operation
- **Indonesian Market Focus**: WIB timezone, local news sources, .JK tickers

## Architecture

### Components

1. **bot_watchlist.py** - Long-running Telegram bot for watchlist management
2. **news_watcher.py** - Scheduled news scanner (runs every 10 min, executes during trading slots)
3. **volume_screener.py** - Scheduled volume spike detector (Mon-Fri 16:20 WIB)

### Trading Slots (WIB)

News scanner only executes during these windows:
- **Slot 1**: 08:45–09:30 (Pre-Market)
- **Slot 2**: 12:00–13:30 (Midday)
- **Slot 3**: 15:15–16:00 (Post-Market)

Outside these slots, the timer still runs but the script exits immediately.

## Installation

### Prerequisites

- Ubuntu server (20.04+)
- Python 3.8+
- Ollama installed with qwen2.5:7b model
- Telegram bot token
- Marketaux API key (free tier)

### Quick Install

```bash
cd /tmp/cc-agent/60593544/project
chmod +x install.sh
./install.sh
```

### Manual Steps After Installation

1. **Configure API Keys**

Edit `/opt/indo_badnews/.env`:

```bash
sudo nano /opt/indo_badnews/.env
```

Required fields:
- `TELEGRAM_BOT_TOKEN` - From @BotFather
- `TELEGRAM_CHAT_ID` - Your chat ID (use @userinfobot)
- `MARKETAUX_API_KEY` - From marketaux.com

2. **Enable Services**

```bash
sudo systemctl enable --now indo_badnews_bot.service
sudo systemctl enable --now indo_badnews.timer
sudo systemctl enable --now indo_volume_screener.timer
```

3. **Verify Installation**

```bash
sudo systemctl status indo_badnews_bot
sudo systemctl list-timers
```

## Configuration Files

### /opt/indo_badnews/.env

```bash
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
MARKETAUX_API_KEY=your_key
OLLAMA_API_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=qwen2.5:7b
MAX_NEWS_AGE_DAYS=3
MAX_TICKERS_PER_RUN=120
TIMEZONE=Asia/Jakarta
```

### Ticker Files

- **ihsg_tickers.txt** - IHSG constituent stocks (always screened)
- **screener_tickers.txt** - Additional tickers to screen
- **watchlist.json** - Auto-managed by bot (per-chat watchlists)

## Usage

### Telegram Bot Commands

```
/wl                    Show your watchlist
/wl BBRI TLKM GOTO     Add tickers
/unwl BBRI TLKM        Remove tickers
/help                  Show help
```

### Manual Testing

**Test News Scanner (Force Run)**

```bash
cd /opt/indo_badnews
source venv/bin/activate
FORCE_RUN=1 python news_watcher.py
```

**Test Volume Screener**

```bash
cd /opt/indo_badnews
source venv/bin/activate
python volume_screener.py
```

**Test Bot (Interactive)**

```bash
cd /opt/indo_badnews
source venv/bin/activate
python bot_watchlist.py
```

## Monitoring

### View Logs

```bash
# Bot logs (real-time)
sudo journalctl -u indo_badnews_bot -f

# News scanner logs
sudo journalctl -u indo_badnews -f

# Volume screener logs
sudo journalctl -u indo_volume_screener -f

# All logs combined
sudo journalctl -u 'indo_*' -f
```

### Check Timer Status

```bash
sudo systemctl list-timers indo_*
```

### Service Status

```bash
sudo systemctl status indo_badnews_bot
sudo systemctl status indo_badnews.timer
sudo systemctl status indo_volume_screener.timer
```

## How It Works

### News Scanner

1. Timer triggers every 10 minutes
2. Script checks if current time is in trading slot
3. If outside slot → exit immediately
4. If inside slot and not run yet → proceed
5. Fetch news from:
   - Marketaux API
   - Google News RSS (general + watchlist tickers)
   - CNBC Indonesia RSS
6. Deduplicate using state.json
7. Classify each article:
   - Check negative keywords
   - If no keyword hit → send to local Ollama AI
8. Send top 5 BAD articles to Telegram
9. Save seen IDs and slot marker to state.json

### Volume Screener

1. Timer triggers Mon-Fri at 09:20 UTC (16:20 WIB)
2. Build ticker universe:
   - All watchlist tickers
   - IHSG tickers
   - Screener tickers
   - Limit to MAX_TICKERS_PER_RUN (120)
3. For each ticker:
   - Fetch 1-month OHLCV from Yahoo
   - Detect 3x volume spike (volume ≥ 3× 20-day avg, price up ≥2%)
   - Classify spike:
     - **SETUP**: ≥3 future days exist, all volumes ≤60% spike
     - **WAIT**: Not enough data or high volume in next 5 days
4. For watchlist tickers only:
   - Detect special patterns:
     - Price↑ ≥1% AND Volume↓ ≥30%
     - Price↓ ≥1% AND Volume↑ ≥30%
5. Send reports to Telegram

### Watchlist Bot

1. Long-running service (restarts on failure)
2. Handles Telegram commands via polling
3. Per-chat watchlist storage in watchlist.json
4. Auto-formats tickers with .JK suffix
5. Used by news scanner and volume screener

## Troubleshooting

### Bot not responding

```bash
sudo systemctl restart indo_badnews_bot
sudo journalctl -u indo_badnews_bot -n 50
```

### News scanner not sending alerts

- Check if current time is in trading slot
- Verify .env configuration
- Test with FORCE_RUN=1
- Check Ollama is running: `curl http://localhost:11434/api/generate`

### Volume screener Yahoo Finance errors

- Reduce MAX_TICKERS_PER_RUN to avoid rate limits
- Check ticker format (must end with .JK)
- Verify tickers exist on Yahoo Finance

### Systemd timer not triggering

```bash
sudo systemctl daemon-reload
sudo systemctl enable indo_badnews.timer
sudo systemctl start indo_badnews.timer
sudo systemctl list-timers
```

## Security Notes

- All services run as your user (not root)
- API keys stored in /opt/indo_badnews/.env (chmod 600 recommended)
- State files are world-readable but contain no sensitive data
- Telegram bot token should never be committed to git

## Performance

- News scanner: ~30-60 seconds per run
- Volume screener: ~2-5 minutes for 120 tickers
- Bot: <10MB RAM idle
- Ollama: Depends on model (qwen2.5:7b ~4GB VRAM)

## Customization

### Add More News Sources

Edit `news_watcher.py`, add to `main()`:

```python
all_articles.extend(fetch_rss_feed(
    "https://your-rss-feed-url.com/rss",
    "Source Name"
))
```

### Change Trading Slots

Edit `news_watcher.py`, modify `TRADING_SLOTS`:

```python
TRADING_SLOTS = [
    {"start": (8, 45), "end": (9, 30), "name": "Pre-Market"},
    # Add more slots...
]
```

### Adjust Volume Spike Threshold

Edit `volume_screener.py`, modify in `detect_volume_spike()`:

```python
if current_volume >= 3 * avg_volume:  # Change 3 to desired multiplier
```

## License

MIT License - Free for personal and commercial use

## Support

For issues or questions:
1. Check logs with journalctl
2. Test components manually
3. Verify .env configuration
4. Check Ollama/Telegram connectivity

---

**Note**: This is a self-hosted solution. You are responsible for server costs, API limits, and data accuracy. Always verify signals independently before trading.
