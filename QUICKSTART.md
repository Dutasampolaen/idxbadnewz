# Quick Start Guide

Get up and running in 15 minutes.

## One-Command Installation

```bash
cd /tmp/cc-agent/60593544/project && chmod +x install.sh && ./install.sh
```

## Configure (2 minutes)

```bash
sudo nano /opt/indo_badnews/.env
```

Replace these 3 values:

```bash
TELEGRAM_BOT_TOKEN=your_bot_token    # From @BotFather
TELEGRAM_CHAT_ID=your_chat_id        # From @userinfobot
MARKETAUX_API_KEY=your_key           # From marketaux.com
```

Save: Ctrl+X, Y, Enter

## Start Services

```bash
sudo systemctl enable --now indo_badnews_bot.service
sudo systemctl enable --now indo_badnews.timer
sudo systemctl enable --now indo_volume_screener.timer
```

## Test (2 minutes)

### 1. Test Telegram Bot

In Telegram, send to your bot:

```
/start
/wl BBRI TLKM
```

Should respond with confirmation.

### 2. Test News Scanner

```bash
cd /opt/indo_badnews
source venv/bin/activate
FORCE_RUN=1 python news_watcher.py
```

Check Telegram for alerts (may take 1-2 minutes).

### 3. Verify Services

```bash
sudo systemctl status indo_badnews_bot
sudo systemctl list-timers indo_*
```

Should show "active" and next run times.

## Done! 🎉

Your system is now running:

- **Watchlist Bot**: Always listening for commands
- **News Scanner**: Checks every 10 min, runs during trading slots
- **Volume Screener**: Runs Mon-Fri at 16:20 WIB

## Telegram Commands

```
/wl                  → Show watchlist
/wl BBRI APEX       → Add tickers
/unwl BBRI          → Remove tickers
/help               → Show help
```

## View Logs

```bash
sudo journalctl -u indo_badnews_bot -f    # Bot logs
sudo journalctl -u indo_badnews -f        # News scanner
sudo journalctl -u indo_volume_screener -f # Volume screener
```

Press Ctrl+C to stop.

## Manual Testing

```bash
cd /opt/indo_badnews
source venv/bin/activate

# Force run news scanner anytime
FORCE_RUN=1 python news_watcher.py

# Run volume screener anytime
python volume_screener.py
```

## Trading Slots (When News Scanner Executes)

- **08:45–09:30 WIB** (Pre-Market)
- **12:00–13:30 WIB** (Midday)
- **15:15–16:00 WIB** (Post-Market)

Outside these times, timer runs but script exits immediately.

## Customize Tickers

```bash
sudo nano /opt/indo_badnews/ihsg_tickers.txt      # Main stocks
sudo nano /opt/indo_badnews/screener_tickers.txt  # Additional stocks
```

One ticker per line (format: `TICKER.JK`)

## Common Issues

### Bot not responding

```bash
sudo systemctl restart indo_badnews_bot
sudo journalctl -u indo_badnews_bot -n 20
```

### No alerts received

- Check if it's during a trading slot: `TZ=Asia/Jakarta date`
- Force run: `FORCE_RUN=1 python news_watcher.py`
- Check logs: `sudo journalctl -u indo_badnews -n 50`

### Ollama not working

```bash
systemctl status ollama
curl http://localhost:11434/api/generate -d '{"model":"qwen2.5:7b","prompt":"test","stream":false}'
```

## File Locations

```
/opt/indo_badnews/
├── .env                    # Configuration
├── news_watcher.py         # News scanner script
├── bot_watchlist.py        # Telegram bot script
├── volume_screener.py      # Volume screener script
├── state.json              # News scanner state
├── watchlist.json          # User watchlists
├── bot_state.json          # Bot update offset
├── ihsg_tickers.txt        # IHSG stocks
└── screener_tickers.txt    # Additional stocks

/etc/systemd/system/
├── indo_badnews_bot.service
├── indo_badnews.service
├── indo_badnews.timer
├── indo_volume_screener.service
└── indo_volume_screener.timer
```

## Useful Commands

```bash
# Check service status
sudo systemctl status indo_badnews_bot

# View all timers
sudo systemctl list-timers

# Restart services
sudo systemctl restart indo_badnews_bot

# View today's logs
sudo journalctl -u 'indo_*' --since today

# Check disk space
df -h /opt/indo_badnews

# Check Python packages
cd /opt/indo_badnews && source venv/bin/activate && pip list
```

## Next Steps

- Read [TESTING.md](TESTING.md) for comprehensive testing
- Read [DEPLOYMENT.md](DEPLOYMENT.md) for production setup
- Read [README.md](README.md) for full documentation

## Support Checklist

If something isn't working:

1. [ ] Check .env is configured correctly
2. [ ] Verify services are active: `sudo systemctl status indo_badnews_bot`
3. [ ] Check timers: `sudo systemctl list-timers indo_*`
4. [ ] View logs: `sudo journalctl -u 'indo_*' -n 50`
5. [ ] Test Ollama: `curl http://localhost:11434/api/generate -d '{"model":"qwen2.5:7b","prompt":"test","stream":false}'`
6. [ ] Test Telegram manually
7. [ ] Run scripts with FORCE_RUN=1

Still stuck? Check the full logs:

```bash
sudo journalctl -u indo_badnews_bot --since "1 hour ago" --no-pager
```

---

**You're all set!** Add some watchlist tickers and wait for alerts. 📊🚨
