# Complete Installation & Testing Checklist

Use this checklist to ensure everything is set up correctly.

## 📋 Pre-Installation Checklist

### System Requirements

- [ ] Ubuntu 20.04 LTS or newer
- [ ] Root or sudo access
- [ ] 2GB+ RAM available
- [ ] 20GB+ disk space available
- [ ] Stable internet connection
- [ ] Python 3.8+ installed (`python3 --version`)
- [ ] Able to install packages (`sudo apt update`)

### Required Credentials

- [ ] Telegram bot token obtained from @BotFather
- [ ] Telegram chat ID obtained (from @userinfobot)
- [ ] Marketaux API key obtained (from marketaux.com free tier)
- [ ] All credentials saved in secure location

### Ollama Setup

- [ ] Ollama installed (`curl -fsSL https://ollama.com/install.sh | sh`)
- [ ] Ollama service running (`systemctl status ollama`)
- [ ] qwen2.5:7b model downloaded (`ollama pull qwen2.5:7b`)
- [ ] Model verified (`ollama list` shows qwen2.5:7b)
- [ ] API responds (`curl http://localhost:11434/api/generate -d '{"model":"qwen2.5:7b","prompt":"test","stream":false}'`)

---

## 📥 Installation Checklist

### Download Files

- [ ] All project files downloaded to local directory
- [ ] Files present:
  - [ ] install.sh
  - [ ] news_watcher.py
  - [ ] bot_watchlist.py
  - [ ] volume_screener.py
  - [ ] requirements.txt
  - [ ] README.md
  - [ ] QUICKSTART.md
  - [ ] TESTING.md
  - [ ] DEPLOYMENT.md

### Run Installer

- [ ] Changed to project directory
- [ ] Made install.sh executable (`chmod +x install.sh`)
- [ ] Ran installer (`./install.sh`)
- [ ] No errors during installation
- [ ] Saw success message "Installation Complete!"

### Verify Installation

- [ ] Directory created: `/opt/indo_badnews` exists
- [ ] Virtual environment created: `/opt/indo_badnews/venv` exists
- [ ] Python scripts copied to `/opt/indo_badnews/`
- [ ] State files created:
  - [ ] state.json
  - [ ] watchlist.json
  - [ ] bot_state.json
- [ ] Ticker files created:
  - [ ] ihsg_tickers.txt
  - [ ] screener_tickers.txt
- [ ] Systemd units installed:
  - [ ] /etc/systemd/system/indo_badnews_bot.service
  - [ ] /etc/systemd/system/indo_badnews.service
  - [ ] /etc/systemd/system/indo_badnews.timer
  - [ ] /etc/systemd/system/indo_volume_screener.service
  - [ ] /etc/systemd/system/indo_volume_screener.timer

---

## ⚙️ Configuration Checklist

### Environment Configuration

- [ ] Edited `/opt/indo_badnews/.env`
- [ ] Set `TELEGRAM_BOT_TOKEN` (from @BotFather)
- [ ] Set `TELEGRAM_CHAT_ID` (your chat ID)
- [ ] Set `MARKETAUX_API_KEY` (from marketaux.com)
- [ ] Verified other settings (OLLAMA_API_URL, OLLAMA_MODEL)
- [ ] File saved correctly

### Verify Environment

```bash
cd /opt/indo_badnews
source venv/bin/activate
python3 -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('Bot Token:', 'OK' if os.getenv('TELEGRAM_BOT_TOKEN') else 'MISSING')
print('Chat ID:', 'OK' if os.getenv('TELEGRAM_CHAT_ID') else 'MISSING')
print('Marketaux:', 'OK' if os.getenv('MARKETAUX_API_KEY') else 'MISSING')
"
```

- [ ] All show "OK"

### Optional: Customize Tickers

- [ ] Reviewed `/opt/indo_badnews/ihsg_tickers.txt`
- [ ] Added/removed tickers as needed
- [ ] Reviewed `/opt/indo_badnews/screener_tickers.txt`
- [ ] Added/removed tickers as needed

---

## 🚀 Service Activation Checklist

### Enable Services

```bash
sudo systemctl enable indo_badnews_bot.service
sudo systemctl enable indo_badnews.timer
sudo systemctl enable indo_volume_screener.timer
```

- [ ] Bot service enabled
- [ ] News timer enabled
- [ ] Volume screener timer enabled
- [ ] No errors during enable

### Start Services

```bash
sudo systemctl start indo_badnews_bot.service
sudo systemctl start indo_badnews.timer
sudo systemctl start indo_volume_screener.timer
```

- [ ] Bot service started
- [ ] News timer started
- [ ] Volume screener timer started
- [ ] No errors during start

### Verify Services

```bash
sudo systemctl status indo_badnews_bot
sudo systemctl status indo_badnews.timer
sudo systemctl status indo_volume_screener.timer
```

- [ ] Bot shows "active (running)"
- [ ] News timer shows "active (waiting)"
- [ ] Volume screener timer shows "active (waiting)"

### Check Timer Schedule

```bash
sudo systemctl list-timers indo_*
```

- [ ] indo_badnews.timer shows next run time
- [ ] indo_volume_screener.timer shows next run time (Mon-Fri 09:20 UTC)
- [ ] Both timers in list

---

## 🧪 Manual Testing Checklist

### Test 1: Watchlist Bot

**In Terminal:**

```bash
cd /opt/indo_badnews
source venv/bin/activate
timeout 10 python bot_watchlist.py || true
```

- [ ] Bot starts without errors
- [ ] Shows "Bot is running..."

**In Telegram:**

- [ ] Send `/start` → Receives help message
- [ ] Send `/wl` → Shows empty watchlist
- [ ] Send `/wl BBRI TLKM` → Confirms addition
- [ ] Send `/wl` → Shows 2 tickers
- [ ] Send `/unwl TLKM` → Confirms removal
- [ ] Send `/wl` → Shows 1 ticker (BBRI)
- [ ] Send `/help` → Shows help message

**Verify:**

```bash
cat /opt/indo_badnews/watchlist.json | jq
```

- [ ] JSON shows your chat ID
- [ ] Shows ["BBRI.JK"]

### Test 2: News Watcher (Force Run)

```bash
cd /opt/indo_badnews
source venv/bin/activate
FORCE_RUN=1 python news_watcher.py
```

- [ ] Script starts
- [ ] Shows "FORCE_RUN mode enabled"
- [ ] Fetches articles from multiple sources
- [ ] Classifies articles (may see "BAD" markers)
- [ ] Completes without errors
- [ ] Check Telegram for alerts (may or may not receive depending on news)

**Verify State:**

```bash
cat /opt/indo_badnews/state.json | jq '.seen | length'
```

- [ ] Shows number > 0 (articles seen)

### Test 3: Volume Screener

```bash
cd /opt/indo_badnews
source venv/bin/activate
python volume_screener.py
```

- [ ] Script starts
- [ ] Loads tickers from watchlist and files
- [ ] Fetches data from Yahoo Finance
- [ ] Processes tickers (shows progress)
- [ ] Completes without errors
- [ ] May send Telegram alerts if spikes found

### Test 4: Systemd Integration

**Manually Trigger Services:**

```bash
sudo systemctl start indo_badnews.service
sudo journalctl -u indo_badnews -f
```

- [ ] Service runs
- [ ] Logs appear in journalctl
- [ ] Completes successfully

```bash
sudo systemctl start indo_volume_screener.service
sudo journalctl -u indo_volume_screener -f
```

- [ ] Service runs
- [ ] Logs appear in journalctl
- [ ] Completes successfully

---

## 📊 Monitoring Setup Checklist

### Log Monitoring

**Test log access:**

```bash
sudo journalctl -u indo_badnews_bot -n 20
sudo journalctl -u indo_badnews -n 20
sudo journalctl -u indo_volume_screener -n 20
```

- [ ] Bot logs visible
- [ ] News scanner logs visible
- [ ] Volume screener logs visible

**Test real-time logs:**

```bash
sudo journalctl -u 'indo_*' -f
```

- [ ] Logs stream in real-time
- [ ] Can see all services
- [ ] Ctrl+C stops streaming

### Health Monitoring

- [ ] Can check service status: `sudo systemctl status indo_badnews_bot`
- [ ] Can list timers: `sudo systemctl list-timers indo_*`
- [ ] Can view recent logs: `sudo journalctl -u 'indo_*' --since today`

---

## 🔒 Security Checklist

### File Permissions

```bash
ls -la /opt/indo_badnews/.env
```

- [ ] File owned by your user
- [ ] Consider setting `chmod 600 /opt/indo_badnews/.env` for extra security

### Service Security

- [ ] Services run as your user (not root)
- [ ] Ollama only listens on localhost
- [ ] No credentials in logs
- [ ] No credentials in systemd units

### API Security

- [ ] Telegram bot token never shared
- [ ] Marketaux key never committed to git
- [ ] .env file not in version control

---

## ✅ Production Readiness Checklist

### Functionality

- [ ] Bot responds to all commands
- [ ] News scanner runs during trading slots
- [ ] Volume screener runs daily (Mon-Fri)
- [ ] Telegram alerts received
- [ ] No critical errors in logs

### Reliability

- [ ] Services auto-start on boot (enabled)
- [ ] Bot auto-restarts on crash (Restart=always)
- [ ] Timers scheduled correctly
- [ ] State persistence working (files update)

### Performance

- [ ] News scanner completes in <2 minutes
- [ ] Volume screener completes in <5 minutes
- [ ] Bot responds instantly
- [ ] System resources adequate (check with `htop`)

### Monitoring

- [ ] Can view logs easily
- [ ] Can check service status
- [ ] Can manually trigger services for testing
- [ ] Timer next-run times visible

### Documentation

- [ ] Read README.md
- [ ] Read QUICKSTART.md
- [ ] Bookmarked TESTING.md for reference
- [ ] Bookmarked DEPLOYMENT.md for reference
- [ ] Know where to find logs

---

## 🎯 Post-Deployment Checklist

### First 24 Hours

- [ ] Received first news alerts during trading slot
- [ ] Received first volume screener report (if Mon-Fri)
- [ ] No service crashes
- [ ] No critical errors in logs
- [ ] Bot responding to commands

### First Week

- [ ] News scanner running consistently during slots
- [ ] Volume screener running daily (Mon-Fri)
- [ ] Watchlist management working
- [ ] Telegram alerts accurate and timely
- [ ] No performance issues

### Ongoing

- [ ] Check logs weekly for errors
- [ ] Update tickers as needed (via Telegram or files)
- [ ] Monitor system resources
- [ ] Backup configuration monthly
- [ ] Update dependencies quarterly

---

## 🆘 Troubleshooting Checklist

If something doesn't work, check:

### Bot Issues

- [ ] Is service running? `sudo systemctl status indo_badnews_bot`
- [ ] Check recent logs: `sudo journalctl -u indo_badnews_bot -n 50`
- [ ] Is bot token correct in .env?
- [ ] Can you reach Telegram API? `curl https://api.telegram.org`
- [ ] Try restart: `sudo systemctl restart indo_badnews_bot`

### News Scanner Issues

- [ ] Is timer active? `sudo systemctl list-timers indo_badnews.timer`
- [ ] Is current time in trading slot? `TZ=Asia/Jakarta date`
- [ ] Try force run: `FORCE_RUN=1 python news_watcher.py`
- [ ] Is Ollama running? `curl http://localhost:11434/api/generate -d '{"model":"qwen2.5:7b","prompt":"test","stream":false}'`
- [ ] Check logs: `sudo journalctl -u indo_badnews -n 50`

### Volume Screener Issues

- [ ] Is timer active? `sudo systemctl list-timers indo_volume_screener.timer`
- [ ] Try manual run: `python volume_screener.py`
- [ ] Are tickers valid (.JK suffix)?
- [ ] Check Yahoo Finance access
- [ ] Reduce MAX_TICKERS_PER_RUN in .env if hitting rate limits

### General Issues

- [ ] Is .env configured correctly?
- [ ] Are all API keys valid?
- [ ] Is network connectivity working?
- [ ] Check disk space: `df -h`
- [ ] Check system resources: `top` or `htop`
- [ ] Review full error logs: `sudo journalctl -u 'indo_*' -p err --since today`

---

## 📝 Final Sign-Off

Before marking as production-ready:

- [ ] All checkboxes above are checked
- [ ] System running smoothly for 24+ hours
- [ ] Received and verified alerts
- [ ] Documentation reviewed and understood
- [ ] Backup plan in place
- [ ] Monitoring setup and tested
- [ ] Know how to restart services if needed
- [ ] Know how to view logs
- [ ] Know how to update configuration

---

## 🎉 Success!

If all checkboxes are checked, congratulations! Your Indonesian Stock Monitoring Stack is production-ready.

**System is live and monitoring:**
- ✅ Bad news alerts during trading slots
- ✅ Volume spike detection daily (Mon-Fri)
- ✅ Watchlist management via Telegram
- ✅ Automated scheduling and reliability

**Next Steps:**
- Add more tickers to your watchlist
- Monitor alerts and refine as needed
- Set up regular backups
- Enjoy automated stock monitoring!

---

**Date Completed**: _______________
**Deployed By**: _______________
**System Status**: ⬜ Testing  ⬜ Staging  ⬜ Production
