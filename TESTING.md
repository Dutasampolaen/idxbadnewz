# Testing Guide

Complete manual testing instructions for the Indonesian Stock Monitoring Stack.

## Prerequisites

Ensure installation is complete:

```bash
cd /opt/indo_badnews
source venv/bin/activate
ls -la
```

You should see:
- `news_watcher.py`
- `bot_watchlist.py`
- `volume_screener.py`
- `.env` (configured with your keys)
- `venv/` directory

## 1. Test News Watcher (Force Run)

The news scanner normally only runs during trading slots. Use `FORCE_RUN=1` to test outside those times.

```bash
cd /opt/indo_badnews
source venv/bin/activate
FORCE_RUN=1 python news_watcher.py
```

**Expected Output:**

```
[2025-11-23 10:30:45 WIB] === Indonesian Bad News Scanner ===
[2025-11-23 10:30:45 WIB] ⚡ FORCE_RUN mode enabled
[2025-11-23 10:30:45 WIB] ✓ Watchlist: 0 tickers
[2025-11-23 10:30:47 WIB] ✓ Fetched 25 articles from Marketaux
[2025-11-23 10:30:49 WIB] ✓ Fetched 50 articles from Google News
[2025-11-23 10:30:51 WIB] ✓ Fetched 30 articles from CNBC Indonesia
[2025-11-23 10:30:51 WIB] ✓ Total articles fetched: 105
[2025-11-23 10:30:51 WIB] ✓ New unseen articles: 105
[2025-11-23 10:30:55 WIB] 🚨 BAD: Bank XYZ mengalami kerugian besar...
[2025-11-23 10:30:58 WIB] 🚨 BAD: Skandal korupsi di perusahaan...
[2025-11-23 10:30:58 WIB] ✓ Bad news articles: 8
[2025-11-23 10:30:59 WIB] ✓ Sent 5 bad news alerts
[2025-11-23 10:30:59 WIB] ✓ State saved
[2025-11-23 10:30:59 WIB] === Scanner Complete ===
```

**Verify:**
- Check your Telegram for the message
- Check `state.json` was updated with seen articles

```bash
cat state.json | jq '.seen | length'
cat state.json | jq '.last_slot'
```

**Test During Trading Slot:**

Wait for a trading slot (08:45-09:30, 12:00-13:30, or 15:15-16:00 WIB) and run without FORCE_RUN:

```bash
python news_watcher.py
```

## 2. Test Volume Screener

```bash
cd /opt/indo_badnews
source venv/bin/activate
python volume_screener.py
```

**Expected Output:**

```
[2025-11-23 16:25:30 WIB] === Indonesian Volume Screener ===
[2025-11-23 16:25:30 WIB] ✓ Watchlist: 5 tickers
[2025-11-23 16:25:30 WIB] ✓ IHSG file: 30 tickers
[2025-11-23 16:25:30 WIB] ✓ Screener file: 5 tickers
[2025-11-23 16:25:30 WIB] ✓ Total tickers to screen: 35
[2025-11-23 16:25:50 WIB] ⏳ Processing 20/35...
[2025-11-23 16:25:55 WIB] 🚀 SETUP: BBRI.JK
[2025-11-23 16:26:02 WIB] ⚠️  Pattern: TLKM.JK - Price↑ Volume↓
[2025-11-23 16:26:15 WIB] ✓ Screening complete
[2025-11-23 16:26:15 WIB] 📊 SETUP spikes: 3
[2025-11-23 16:26:15 WIB] ⏳ WAIT spikes: 5
[2025-11-23 16:26:15 WIB] ⚠️  Watchlist patterns: 2
[2025-11-23 16:26:16 WIB] ✓ Sent 2 report(s)
[2025-11-23 16:26:16 WIB] === Screener Complete ===
```

**Verify:**
- Check Telegram for volume spike reports
- Verify tickers from all sources were processed

## 3. Test Watchlist Bot (Interactive)

Open terminal and run bot:

```bash
cd /opt/indo_badnews
source venv/bin/activate
python bot_watchlist.py
```

**Expected Output:**

```
[2025-11-23 16:30:00] 🤖 Starting Indonesian Stock Watchlist Bot...
[2025-11-23 16:30:01] ✓ Bot handlers registered
[2025-11-23 16:30:01] ✓ Bot is running... Press Ctrl+C to stop
```

**Test Commands in Telegram:**

1. Send `/start` → Should show help message
2. Send `/wl` → Should show empty watchlist
3. Send `/wl BBRI TLKM GOTO` → Should add 3 tickers
4. Send `/wl` → Should show 3 tickers
5. Send `/unwl TLKM` → Should remove 1 ticker
6. Send `/wl` → Should show 2 tickers
7. Send `/help` → Should show help

**Expected Bot Logs:**

```
[2025-11-23 16:31:25] Chat 123456789: Added ['BBRI.JK', 'TLKM.JK', 'GOTO.JK']
[2025-11-23 16:31:45] Chat 123456789: Removed ['TLKM.JK']
```

**Verify:**

```bash
cat watchlist.json | jq
```

Should show your chat ID with tickers.

Press Ctrl+C to stop the bot.

## 4. Test Systemd Services

### Check Service Status

```bash
sudo systemctl status indo_badnews_bot
sudo systemctl status indo_badnews.timer
sudo systemctl status indo_volume_screener.timer
```

All should show "active" status.

### Check Timer Schedule

```bash
sudo systemctl list-timers indo_*
```

**Expected Output:**

```
NEXT                         LEFT       LAST                         PASSED  UNIT
Mon 2025-11-25 09:20:00 UTC  16h left   n/a                          n/a     indo_volume_screener.timer
Mon 2025-11-25 02:35:00 WIB  3min left  Mon 2025-11-25 02:25:00 WIB  6min ago indo_badnews.timer
```

### View Service Logs

**Bot Logs (Real-time):**

```bash
sudo journalctl -u indo_badnews_bot -f
```

Press Ctrl+C to stop following.

**News Scanner Logs (Last 50 lines):**

```bash
sudo journalctl -u indo_badnews -n 50
```

**Volume Screener Logs:**

```bash
sudo journalctl -u indo_volume_screener -n 50
```

**All Logs Combined:**

```bash
sudo journalctl -u 'indo_*' --since today
```

### Manually Trigger Timer

**Trigger News Scanner:**

```bash
sudo systemctl start indo_badnews.service
```

Watch logs:

```bash
sudo journalctl -u indo_badnews -f
```

**Trigger Volume Screener:**

```bash
sudo systemctl start indo_volume_screener.service
```

Watch logs:

```bash
sudo journalctl -u indo_volume_screener -f
```

## 5. Test Ollama Integration

Verify Ollama is running and model is available:

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:7b",
  "prompt": "Classify this as BAD or OK: Perusahaan mengalami kerugian besar",
  "stream": false
}'
```

**Expected Response:**

```json
{
  "model": "qwen2.5:7b",
  "response": "BAD",
  ...
}
```

## 6. Test Edge Cases

### Empty Watchlist

```bash
echo '{}' > /opt/indo_badnews/watchlist.json
python news_watcher.py
```

Should run without errors, just skip watchlist-specific news.

### Invalid Ticker

In Telegram, send:

```
/wl INVALID123
```

Bot should add it, but screener will skip it (Yahoo Finance won't find data).

### Outside Trading Slot

Run news scanner without FORCE_RUN outside 08:45-09:30, 12:00-13:30, 15:15-16:00 WIB:

```bash
python news_watcher.py
```

**Expected:**

```
[2025-11-23 03:00:00 WIB] === Indonesian Bad News Scanner ===
[2025-11-23 03:00:00 WIB] ⏸️  Outside trading slots, exiting
```

### Duplicate Slot Run

Run twice during same slot:

```bash
FORCE_RUN=1 python news_watcher.py
python news_watcher.py  # Same slot
```

Second run should exit immediately (already ran for this slot).

## 7. Test State Files

### state.json (News Scanner)

```bash
cat /opt/indo_badnews/state.json | jq
```

Should contain:
- `seen`: Array of article IDs
- `last_slot`: Last executed slot ID

### watchlist.json (Watchlist Bot)

```bash
cat /opt/indo_badnews/watchlist.json | jq
```

Should contain chat IDs as keys, arrays of tickers as values.

### bot_state.json (Bot Offset)

```bash
cat /opt/indo_badnews/bot_state.json | jq
```

Should contain:
- `offset`: Last processed Telegram update ID

## 8. Performance Test

### Large Ticker List

Add 100 tickers to screener_tickers.txt:

```bash
cd /opt/indo_badnews
for i in {1..100}; do echo "TICKER${i}.JK" >> screener_tickers.txt; done
```

Run screener with timing:

```bash
time python volume_screener.py
```

Should complete in <5 minutes (most tickers will fail, that's OK).

Clean up:

```bash
rm screener_tickers.txt
cat > screener_tickers.txt <<EOF
ARTO.JK
APEX.JK
AKRA.JK
EOF
```

## 9. Restart Services

After testing, restart all services:

```bash
sudo systemctl restart indo_badnews_bot
sudo systemctl daemon-reload
```

## 10. Complete Integration Test

1. Add watchlist via Telegram: `/wl BBRI TLKM`
2. Wait for next trading slot OR run with FORCE_RUN
3. Check Telegram for news alerts about BBRI or TLKM
4. Wait until 16:20 WIB (09:20 UTC) on weekday OR run screener manually
5. Check Telegram for volume spike reports

## Troubleshooting

### Telegram not sending messages

```bash
# Test manually
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d "chat_id=${TELEGRAM_CHAT_ID}" \
  -d "text=Test message"
```

### Python import errors

```bash
cd /opt/indo_badnews
source venv/bin/activate
pip install -r requirements.txt
```

### Systemd service not starting

```bash
sudo systemctl daemon-reload
sudo systemctl reset-failed indo_badnews_bot
sudo systemctl start indo_badnews_bot
sudo journalctl -u indo_badnews_bot -n 100
```

### Timezone issues

Verify system timezone:

```bash
timedatectl
```

Should show UTC. Scripts handle WIB conversion internally.

## Success Criteria

✅ News scanner runs and sends alerts (with FORCE_RUN)
✅ Volume screener completes and sends reports
✅ Bot responds to all commands
✅ Systemd services are active
✅ Timers show correct next run times
✅ Logs show no critical errors
✅ Telegram receives messages
✅ State files update correctly
✅ Ollama AI classifications work

If all criteria pass, your system is ready for production!
