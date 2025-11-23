# Deployment Guide

Complete production deployment guide for Ubuntu servers.

## Server Requirements

- **OS**: Ubuntu 20.04 LTS or newer
- **RAM**: 2GB minimum (8GB recommended with Ollama)
- **CPU**: 2 cores minimum
- **Storage**: 20GB minimum
- **Network**: Stable internet connection
- **GPU**: Optional (for faster Ollama inference)

## Pre-Installation Checklist

### 1. Install System Dependencies

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip curl git
```

### 2. Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 3. Download AI Model

```bash
ollama pull qwen2.5:7b
```

Verify installation:

```bash
ollama list
```

Should show `qwen2.5:7b` in the list.

### 4. Get API Credentials

#### Telegram Bot Token

1. Open Telegram and search for `@BotFather`
2. Send `/newbot`
3. Follow prompts to create bot
4. Save the token (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

#### Telegram Chat ID

1. Start a chat with your new bot
2. Search for `@userinfobot`
3. Send any message
4. Note your chat ID (format: `123456789`)

#### Marketaux API Key

1. Go to https://www.marketaux.com/
2. Sign up for free account
3. Get API key from dashboard

## Installation Steps

### Step 1: Download Installation Files

```bash
# Clone or download the project files
cd ~
mkdir -p indo-badnews-deploy
cd indo-badnews-deploy

# Copy all files here:
# - install.sh
# - news_watcher.py
# - bot_watchlist.py
# - volume_screener.py
```

### Step 2: Run Installation Script

```bash
chmod +x install.sh
./install.sh
```

This will:
- Create `/opt/indo_badnews` directory
- Set up Python virtual environment
- Install all dependencies
- Create sample ticker files
- Install systemd services and timers
- Initialize state files

### Step 3: Configure Environment

```bash
sudo nano /opt/indo_badnews/.env
```

Replace placeholders with your actual credentials:

```bash
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
MARKETAUX_API_KEY=your_marketaux_key_here
OLLAMA_API_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=qwen2.5:7b
MAX_NEWS_AGE_DAYS=3
MAX_TICKERS_PER_RUN=120
TIMEZONE=Asia/Jakarta
```

Save and exit (Ctrl+X, Y, Enter).

### Step 4: Verify Configuration

```bash
cd /opt/indo_badnews
source venv/bin/activate

# Test environment loading
python3 -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('Bot Token:', 'OK' if os.getenv('TELEGRAM_BOT_TOKEN') else 'MISSING')
print('Chat ID:', 'OK' if os.getenv('TELEGRAM_CHAT_ID') else 'MISSING')
print('Marketaux:', 'OK' if os.getenv('MARKETAUX_API_KEY') else 'MISSING')
"
```

All should show "OK".

### Step 5: Test Components Manually

See [TESTING.md](TESTING.md) for detailed testing procedures.

Quick tests:

```bash
# Test news scanner (force run)
FORCE_RUN=1 python news_watcher.py

# Test volume screener
python volume_screener.py

# Test bot (interactive - press Ctrl+C after few seconds)
timeout 10 python bot_watchlist.py || true
```

### Step 6: Enable Services

```bash
sudo systemctl enable indo_badnews_bot.service
sudo systemctl enable indo_badnews.timer
sudo systemctl enable indo_volume_screener.timer
```

### Step 7: Start Services

```bash
sudo systemctl start indo_badnews_bot.service
sudo systemctl start indo_badnews.timer
sudo systemctl start indo_volume_screener.timer
```

### Step 8: Verify Services

```bash
sudo systemctl status indo_badnews_bot
sudo systemctl status indo_badnews.timer
sudo systemctl status indo_volume_screener.timer
```

All should show "active".

### Step 9: Check Timer Schedule

```bash
sudo systemctl list-timers indo_*
```

Should show:
- `indo_badnews.timer` - Next run in <10 minutes
- `indo_volume_screener.timer` - Next run at Mon-Fri 09:20 UTC

## Post-Deployment Configuration

### Customize Ticker Lists

#### IHSG Tickers (Main Index)

```bash
sudo nano /opt/indo_badnews/ihsg_tickers.txt
```

Add one ticker per line (format: `TICKER.JK`).

#### Additional Screener Tickers

```bash
sudo nano /opt/indo_badnews/screener_tickers.txt
```

### Adjust Timing

#### Change News Scanner Frequency

Edit timer unit:

```bash
sudo nano /etc/systemd/system/indo_badnews.timer
```

Modify `OnUnitActiveSec=10min` to desired interval.

#### Change Volume Screener Time

Edit timer unit:

```bash
sudo nano /etc/systemd/system/indo_volume_screener.timer
```

Modify `OnCalendar=Mon-Fri 09:20:00 UTC` (remember: UTC = WIB - 7 hours).

After editing timers:

```bash
sudo systemctl daemon-reload
sudo systemctl restart indo_badnews.timer
sudo systemctl restart indo_volume_screener.timer
```

### Adjust Configuration

Edit `/opt/indo_badnews/.env`:

```bash
# Increase news age window
MAX_NEWS_AGE_DAYS=7

# Reduce tickers per run to avoid rate limits
MAX_TICKERS_PER_RUN=50
```

Restart services after changes:

```bash
sudo systemctl restart indo_badnews_bot
```

## Monitoring

### Real-time Log Monitoring

```bash
# All services
sudo journalctl -u 'indo_*' -f

# Individual services
sudo journalctl -u indo_badnews_bot -f
sudo journalctl -u indo_badnews -f
sudo journalctl -u indo_volume_screener -f
```

### Check Recent Logs

```bash
# Today's logs
sudo journalctl -u 'indo_*' --since today

# Last hour
sudo journalctl -u 'indo_*' --since "1 hour ago"

# Last 100 lines
sudo journalctl -u indo_badnews_bot -n 100
```

### Service Health Check

Create a monitoring script:

```bash
cat > /opt/indo_badnews/health_check.sh <<'EOF'
#!/bin/bash
echo "=== Service Health Check ==="
echo ""

echo "1. Bot Service:"
systemctl is-active indo_badnews_bot.service

echo "2. News Timer:"
systemctl is-active indo_badnews.timer

echo "3. Volume Timer:"
systemctl is-active indo_volume_screener.timer

echo ""
echo "4. Next Timer Runs:"
systemctl list-timers indo_* --no-pager

echo ""
echo "5. Recent Errors:"
journalctl -u 'indo_*' --since "1 hour ago" -p err --no-pager | tail -20

echo ""
echo "=== Check Complete ==="
EOF

chmod +x /opt/indo_badnews/health_check.sh
```

Run health check:

```bash
/opt/indo_badnews/health_check.sh
```

## Backup and Restore

### Backup

```bash
#!/bin/bash
BACKUP_DIR=~/indo-badnews-backup-$(date +%Y%m%d)
mkdir -p $BACKUP_DIR

# Backup configuration and state
cp /opt/indo_badnews/.env $BACKUP_DIR/
cp /opt/indo_badnews/state.json $BACKUP_DIR/
cp /opt/indo_badnews/watchlist.json $BACKUP_DIR/
cp /opt/indo_badnews/bot_state.json $BACKUP_DIR/
cp /opt/indo_badnews/ihsg_tickers.txt $BACKUP_DIR/
cp /opt/indo_badnews/screener_tickers.txt $BACKUP_DIR/

# Backup systemd units
cp /etc/systemd/system/indo_*.{service,timer} $BACKUP_DIR/

echo "Backup saved to: $BACKUP_DIR"
```

### Restore

```bash
#!/bin/bash
BACKUP_DIR=~/indo-badnews-backup-YYYYMMDD  # Replace with actual backup dir

# Restore configuration
cp $BACKUP_DIR/.env /opt/indo_badnews/
cp $BACKUP_DIR/state.json /opt/indo_badnews/
cp $BACKUP_DIR/watchlist.json /opt/indo_badnews/
cp $BACKUP_DIR/bot_state.json /opt/indo_badnews/
cp $BACKUP_DIR/ihsg_tickers.txt /opt/indo_badnews/
cp $BACKUP_DIR/screener_tickers.txt /opt/indo_badnews/

# Restart services
sudo systemctl restart indo_badnews_bot
sudo systemctl daemon-reload

echo "Restore complete"
```

## Updating

### Update Python Scripts

```bash
cd /opt/indo_badnews

# Backup current version
cp news_watcher.py news_watcher.py.bak
cp bot_watchlist.py bot_watchlist.py.bak
cp volume_screener.py volume_screener.py.bak

# Copy new versions
# ... copy updated scripts here ...

# Restart services
sudo systemctl restart indo_badnews_bot
```

### Update Dependencies

```bash
cd /opt/indo_badnews
source venv/bin/activate
pip install --upgrade -r requirements.txt
deactivate

sudo systemctl restart indo_badnews_bot
```

### Update Ollama Model

```bash
ollama pull qwen2.5:7b
```

## Uninstallation

```bash
# Stop and disable services
sudo systemctl stop indo_badnews_bot
sudo systemctl stop indo_badnews.timer
sudo systemctl stop indo_volume_screener.timer
sudo systemctl disable indo_badnews_bot
sudo systemctl disable indo_badnews.timer
sudo systemctl disable indo_volume_screener.timer

# Remove systemd units
sudo rm /etc/systemd/system/indo_badnews*
sudo systemctl daemon-reload

# Remove application directory
sudo rm -rf /opt/indo_badnews

echo "Uninstallation complete"
```

## Security Best Practices

### 1. Protect Configuration File

```bash
sudo chmod 600 /opt/indo_badnews/.env
sudo chown $USER:$USER /opt/indo_badnews/.env
```

### 2. Firewall Rules

If running on public server:

```bash
sudo ufw allow 22/tcp  # SSH
sudo ufw enable
```

Ollama should only listen on localhost (default).

### 3. Regular Updates

```bash
sudo apt update && sudo apt upgrade -y
```

### 4. Log Rotation

Systemd handles log rotation automatically, but you can check:

```bash
sudo journalctl --vacuum-time=30d  # Keep 30 days
sudo journalctl --vacuum-size=500M  # Keep max 500MB
```

## Troubleshooting Common Issues

### Bot Not Starting

```bash
# Check logs
sudo journalctl -u indo_badnews_bot -n 50

# Verify token
cd /opt/indo_badnews
source venv/bin/activate
python3 -c "
from dotenv import load_dotenv
import os
load_dotenv()
print(os.getenv('TELEGRAM_BOT_TOKEN'))
"
```

### News Scanner Not Running During Slot

```bash
# Check current WIB time
TZ=Asia/Jakarta date

# Manually trigger
sudo systemctl start indo_badnews.service
sudo journalctl -u indo_badnews -f
```

### Volume Screener Yahoo Errors

```bash
# Reduce ticker count
nano /opt/indo_badnews/.env
# Set MAX_TICKERS_PER_RUN=50

sudo systemctl restart indo_badnews.timer
```

### Ollama Not Responding

```bash
# Check Ollama service
systemctl status ollama

# Restart Ollama
sudo systemctl restart ollama

# Test manually
curl http://localhost:11434/api/generate -d '{"model":"qwen2.5:7b","prompt":"test","stream":false}'
```

### Timer Not Triggering

```bash
# Check timer status
sudo systemctl status indo_badnews.timer

# Enable and start
sudo systemctl enable --now indo_badnews.timer

# Force trigger
sudo systemctl start indo_badnews.service
```

## Performance Optimization

### 1. Reduce Ticker Count

Edit `.env`:

```bash
MAX_TICKERS_PER_RUN=50
```

### 2. Increase Timer Intervals

Edit timer units to run less frequently.

### 3. Use Smaller AI Model

Edit `.env`:

```bash
OLLAMA_MODEL=qwen2.5:3b  # Smaller, faster
```

Then:

```bash
ollama pull qwen2.5:3b
```

### 4. Limit News Sources

Edit `news_watcher.py`, comment out sources you don't need.

## Production Checklist

- [ ] Ubuntu server prepared
- [ ] Ollama installed with qwen2.5:7b
- [ ] API credentials obtained
- [ ] Installation script completed
- [ ] .env configured correctly
- [ ] Manual tests passed
- [ ] Services enabled and started
- [ ] Timers scheduled correctly
- [ ] Telegram bot responding
- [ ] First alerts received
- [ ] Logs monitoring set up
- [ ] Backup script created
- [ ] Health check script working

## Support

For issues:

1. Check logs: `sudo journalctl -u 'indo_*' -n 100`
2. Verify configuration: `cat /opt/indo_badnews/.env`
3. Test manually: See [TESTING.md](TESTING.md)
4. Check Ollama: `curl http://localhost:11434/api/generate -d '{"model":"qwen2.5:7b","prompt":"test","stream":false}'`
5. Verify Telegram: Test bot manually

---

**Ready for Production!** 🚀
