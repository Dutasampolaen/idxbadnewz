#!/bin/bash
# One-line installer for Indonesian Stock Monitoring Stack
set -e

REPO_URL="https://github.com/YOUR_USERNAME/indo-stock-monitor"
INSTALL_DIR="$HOME/indo-stock-monitor"

echo "================================================"
echo "Indonesian Stock Monitoring Stack - Quick Install"
echo "================================================"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Installing..."
    sudo apt update && sudo apt install -y git
fi

# Clone repository
if [ -d "$INSTALL_DIR" ]; then
    echo "⚠️  Directory $INSTALL_DIR already exists. Removing..."
    rm -rf "$INSTALL_DIR"
fi

echo "📥 Cloning repository..."
git clone "$REPO_URL" "$INSTALL_DIR"

# Run installer
cd "$INSTALL_DIR"
chmod +x install.sh

echo ""
echo "🚀 Running installer..."
./install.sh

echo ""
echo "================================================"
echo "✅ Installation Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Configure API keys:"
echo "   sudo nano /opt/indo_badnews/.env"
echo ""
echo "2. Enable and start services:"
echo "   sudo systemctl enable --now indo_badnews_bot.service"
echo "   sudo systemctl enable --now indo_badnews.timer"
echo "   sudo systemctl enable --now indo_volume_screener.timer"
echo ""
echo "3. Check status:"
echo "   sudo systemctl status indo_badnews_bot"
echo ""
echo "See $INSTALL_DIR/QUICKSTART.md for detailed setup."
echo ""
