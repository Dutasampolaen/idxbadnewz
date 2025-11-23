# Install from GitHub

## One-Line Install Command

```bash
curl -fsSL https://raw.githubusercontent.com/Dutasampolaen/idxbadnewz/main/install.sh | bash
```

---

## Recommended: Clone and Inspect First

For security, it's better to clone the repository and inspect the code before running:

### Option 1: HTTPS Clone (Recommended for most users)

```bash
git clone https://github.com/Dutasampolaen/idxbadnewz.git
cd idxbadnewz
chmod +x install.sh
./install.sh
```

### Option 2: SSH Clone (If you have SSH keys set up)

```bash
git clone git@github.com:Dutasampolaen/idxbadnewz.git
cd idxbadnewz
chmod +x install.sh
./install.sh
```

### Option 3: Download ZIP (No git required)

```bash
wget https://github.com/Dutasampolaen/idxbadnewz/archive/refs/heads/main.zip
unzip main.zip
cd idxbadnewz-main
chmod +x install.sh
./install.sh
```

---

## Complete Installation Steps

### 1. Prerequisites

Ensure you have these installed:

```bash
# Update system
sudo apt update

# Install required packages
sudo apt install -y git python3 python3-venv python3-pip curl

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Download AI model
ollama pull qwen2.5:7b
```

### 2. Clone Repository

```bash
git clone https://github.com/Dutasampolaen/idxbadnewz.git
cd idxbadnewz
```

### 3. Run Installer

```bash
chmod +x install.sh
./install.sh
```

The installer will:
- ✅ Create `/opt/indo_badnews` directory
- ✅ Set up Python virtual environment
- ✅ Install all dependencies
- ✅ Copy Python scripts
- ✅ Create sample ticker files
- ✅ Install systemd services and timers
- ✅ Create configuration template

### 4. Configure API Keys

```bash
sudo nano /opt/indo_badnews/.env
```

Add your credentials:

```bash
TELEGRAM_BOT_TOKEN=your_bot_token_from_@BotFather
TELEGRAM_CHAT_ID=your_chat_id_from_@userinfobot
MARKETAUX_API_KEY=your_key_from_marketaux.com
```

Save: `Ctrl+X`, `Y`, `Enter`

### 5. Enable and Start Services

```bash
sudo systemctl enable --now indo_badnews_bot.service
sudo systemctl enable --now indo_badnews.timer
sudo systemctl enable --now indo_volume_screener.timer
```

### 6. Verify Installation

```bash
# Check service status
sudo systemctl status indo_badnews_bot

# Check timers
sudo systemctl list-timers indo_*

# View logs
sudo journalctl -u indo_badnews_bot -f
```

### 7. Test Telegram Bot

In Telegram, send to your bot:

```
/start
/wl BBRI TLKM
```

Should receive confirmation messages.

### 8. Test News Scanner

```bash
cd /opt/indo_badnews
source venv/bin/activate
FORCE_RUN=1 python news_watcher.py
```

Check Telegram for alerts.

---

## Quick Commands After Installation

### View Logs

```bash
# Real-time logs (all services)
sudo journalctl -u 'indo_*' -f

# Bot logs only
sudo journalctl -u indo_badnews_bot -f

# Last 50 lines
sudo journalctl -u indo_badnews_bot -n 50
```

### Restart Services

```bash
sudo systemctl restart indo_badnews_bot
```

### Check Status

```bash
sudo systemctl status indo_badnews_bot
sudo systemctl list-timers indo_*
```

### Manual Testing

```bash
cd /opt/indo_badnews
source venv/bin/activate

# Force run news scanner
FORCE_RUN=1 python news_watcher.py

# Run volume screener
python volume_screener.py
```

---

## Troubleshooting

### Installation Failed

```bash
# Check logs
cat /tmp/indo_install.log

# Try manual installation
cd /opt
sudo mkdir indo_badnews
sudo chown $USER:$USER indo_badnews
cd indo_badnews
python3 -m venv venv
source venv/bin/activate
pip install -r ~/indo-stock-monitor/requirements.txt
```

### Services Not Starting

```bash
# Check systemd status
sudo systemctl status indo_badnews_bot

# Check logs
sudo journalctl -u indo_badnews_bot -n 50

# Verify .env configuration
cat /opt/indo_badnews/.env
```

### Ollama Not Working

```bash
# Check Ollama status
systemctl status ollama

# Test Ollama
curl http://localhost:11434/api/generate -d '{"model":"qwen2.5:7b","prompt":"test","stream":false}'

# Restart Ollama
sudo systemctl restart ollama
```

---

## Update Installation

To update to the latest version:

```bash
cd ~/idxbadnewz  # Or wherever you cloned it
git pull origin main
cd /opt/indo_badnews

# Backup current version
cp news_watcher.py news_watcher.py.bak
cp bot_watchlist.py bot_watchlist.py.bak
cp volume_screener.py volume_screener.py.bak

# Copy new versions
cp ~/idxbadnewz/*.py /opt/indo_badnews/

# Restart services
sudo systemctl restart indo_badnews_bot
```

---

## Uninstall

```bash
# Stop and disable services
sudo systemctl stop indo_badnews_bot indo_badnews.timer indo_volume_screener.timer
sudo systemctl disable indo_badnews_bot indo_badnews.timer indo_volume_screener.timer

# Remove systemd units
sudo rm /etc/systemd/system/indo_*
sudo systemctl daemon-reload

# Remove application
sudo rm -rf /opt/indo_badnews

# Remove cloned repository (optional)
rm -rf ~/idxbadnewz
```

---

## Security Notes

⚠️ **Never commit sensitive data:**
- `.env` file is in `.gitignore`
- State files (`*.json`) are in `.gitignore`
- Always review code before running installation scripts

✅ **Best practices:**
- Clone and inspect code before running
- Use HTTPS clone for public repositories
- Use SSH clone if you have SSH keys set up
- Regularly update dependencies

---

## Repository Structure

```
idxbadnewz/
├── README.md                  # Main documentation
├── QUICKSTART.md             # Fast setup guide
├── INSTALL_FROM_GITHUB.md    # This file
├── install.sh                # Installation script
├── requirements.txt          # Python dependencies
├── news_watcher.py           # News scanner
├── bot_watchlist.py          # Telegram bot
├── volume_screener.py        # Volume screener
├── TESTING.md                # Testing guide
├── DEPLOYMENT.md             # Production deployment
├── CHECKLIST.md              # Installation checklist
├── SUMMARY.md                # Executive summary
├── ARCHITECTURE.txt          # System architecture
├── QUICK_REFERENCE.txt       # Command reference
├── INDEX.md                  # Documentation index
└── .gitignore                # Git ignore rules
```

---

## Support

- **Documentation**: Start with `INDEX.md`
- **Quick Setup**: See `QUICKSTART.md`
- **Troubleshooting**: See `QUICK_REFERENCE.txt`
- **Issues**: Check logs with `sudo journalctl -u 'indo_*' -n 100`

---

**Ready to install!** 🚀

Start with the clone method above, then follow the numbered steps.
