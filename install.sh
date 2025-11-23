#!/bin/bash
set -e

echo "Installing Indonesian Stock Monitoring Stack..."

# Create base directory
sudo mkdir -p /opt/indo_badnews
sudo chown $USER:$USER /opt/indo_badnews
cd /opt/indo_badnews

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Create requirements file
cat > requirements.txt <<EOF
python-telegram-bot==20.7
feedparser==6.0.10
requests==2.31.0
yfinance==0.2.32
python-dotenv==1.0.0
pytz==2023.3
python-dateutil==2.8.2
EOF

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

echo "✓ Virtual environment and dependencies installed"

# Create sample ticker files
cat > ihsg_tickers.txt <<EOF
BBCA.JK
BBRI.JK
BMRI.JK
TLKM.JK
ASII.JK
UNVR.JK
ICBP.JK
INDF.JK
KLBF.JK
SMGR.JK
ADRO.JK
PTBA.JK
INCO.JK
ANTM.JK
BYAN.JK
EXCL.JK
ISAT.JK
PGAS.JK
JSMR.JK
WIKA.JK
WSKT.JK
PTPP.JK
BBTN.JK
BBNI.JK
BRIS.JK
ACES.JK
GOTO.JK
BREN.JK
EMTK.JK
MEDC.JK
EOF

cat > screener_tickers.txt <<EOF
ARTO.JK
APEX.JK
AKRA.JK
AMRT.JK
BUKA.JK
EOF

echo "✓ Sample ticker files created"

# Create .env template
cat > .env <<EOF
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# News API Configuration
MARKETAUX_API_KEY=your_marketaux_key_here

# Ollama Configuration (local)
OLLAMA_API_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=qwen2.5:7b

# Configuration
MAX_NEWS_AGE_DAYS=3
MAX_TICKERS_PER_RUN=120
TIMEZONE=Asia/Jakarta
EOF

echo "✓ Environment template created"
echo ""
echo "⚠️  IMPORTANT: Edit /opt/indo_badnews/.env with your API keys!"
echo ""

# Create initial state files
echo '{"seen": [], "last_slot": null}' > state.json
echo '{}' > watchlist.json
echo '{"offset": 0}' > bot_state.json

echo "✓ State files initialized"

# Copy Python scripts from deployment package
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$SCRIPT_DIR/news_watcher.py" ]; then
    cp "$SCRIPT_DIR/news_watcher.py" /opt/indo_badnews/
    cp "$SCRIPT_DIR/bot_watchlist.py" /opt/indo_badnews/
    cp "$SCRIPT_DIR/volume_screener.py" /opt/indo_badnews/
    chmod +x /opt/indo_badnews/*.py
    echo "✓ Python scripts copied"
else
    echo "⚠️  Python scripts not found in $SCRIPT_DIR"
    echo "   Please manually copy:"
    echo "   - news_watcher.py"
    echo "   - bot_watchlist.py"
    echo "   - volume_screener.py"
    echo "   to /opt/indo_badnews/"
fi

# Install systemd services
sudo tee /etc/systemd/system/indo_badnews_bot.service > /dev/null <<EOF
[Unit]
Description=Indonesian Stock Watchlist Telegram Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/indo_badnews
Environment="PATH=/opt/indo_badnews/venv/bin"
ExecStart=/opt/indo_badnews/venv/bin/python /opt/indo_badnews/bot_watchlist.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/indo_badnews.service > /dev/null <<EOF
[Unit]
Description=Indonesian Bad News Scanner (oneshot)
After=network.target

[Service]
Type=oneshot
User=$USER
WorkingDirectory=/opt/indo_badnews
Environment="PATH=/opt/indo_badnews/venv/bin"
ExecStart=/opt/indo_badnews/venv/bin/python /opt/indo_badnews/news_watcher.py
EOF

sudo tee /etc/systemd/system/indo_badnews.timer > /dev/null <<EOF
[Unit]
Description=Indonesian Bad News Scanner Timer (every 10 minutes)

[Timer]
OnBootSec=2min
OnUnitActiveSec=10min
AccuracySec=1min

[Install]
WantedBy=timers.target
EOF

sudo tee /etc/systemd/system/indo_volume_screener.service > /dev/null <<EOF
[Unit]
Description=Indonesian Volume Screener (oneshot)
After=network.target

[Service]
Type=oneshot
User=$USER
WorkingDirectory=/opt/indo_badnews
Environment="PATH=/opt/indo_badnews/venv/bin"
ExecStart=/opt/indo_badnews/venv/bin/python /opt/indo_badnews/volume_screener.py
EOF

sudo tee /etc/systemd/system/indo_volume_screener.timer > /dev/null <<EOF
[Unit]
Description=Indonesian Volume Screener Timer (Mon-Fri 16:20 WIB)

[Timer]
OnCalendar=Mon-Fri 09:20:00 UTC
AccuracySec=1min

[Install]
WantedBy=timers.target
EOF

echo "✓ Systemd services and timers installed"

# Reload systemd
sudo systemctl daemon-reload

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit /opt/indo_badnews/.env with your API keys"
echo "2. Enable and start services:"
echo "   sudo systemctl enable --now indo_badnews_bot.service"
echo "   sudo systemctl enable --now indo_badnews.timer"
echo "   sudo systemctl enable --now indo_volume_screener.timer"
echo ""
echo "3. Check status:"
echo "   sudo systemctl status indo_badnews_bot"
echo "   sudo systemctl list-timers"
echo ""
echo "4. View logs:"
echo "   sudo journalctl -u indo_badnews_bot -f"
echo "   sudo journalctl -u indo_badnews -f"
echo "   sudo journalctl -u indo_volume_screener -f"
echo ""
