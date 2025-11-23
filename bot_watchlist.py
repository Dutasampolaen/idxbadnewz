#!/usr/bin/env python3
"""
Indonesian Stock Watchlist Telegram Bot
Long-running service that handles watchlist management commands.
"""

import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WATCHLIST_FILE = Path("/opt/indo_badnews/watchlist.json")
BOT_STATE_FILE = Path("/opt/indo_badnews/bot_state.json")


def log(msg):
    """Print timestamped log message"""
    from datetime import datetime
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")


def load_watchlist():
    """Load watchlist from disk"""
    if WATCHLIST_FILE.exists():
        with open(WATCHLIST_FILE, "r") as f:
            return json.load(f)
    return {}


def save_watchlist(data):
    """Save watchlist to disk"""
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(data, f, indent=2)


def normalize_ticker(ticker):
    """Normalize ticker format (add .JK if missing)"""
    ticker = ticker.upper().strip()
    if not ticker.endswith(".JK"):
        ticker += ".JK"
    return ticker


async def cmd_wl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /wl command - show or add tickers"""
    chat_id = str(update.effective_chat.id)
    args = context.args

    watchlist = load_watchlist()
    chat_watchlist = watchlist.get(chat_id, [])

    if not args:
        if chat_watchlist:
            tickers_str = ", ".join(chat_watchlist)
            await update.message.reply_text(
                f"📊 Your watchlist ({len(chat_watchlist)}):\n{tickers_str}"
            )
        else:
            await update.message.reply_text(
                "📊 Your watchlist is empty.\n\n"
                "Add tickers with: /wl BBRI TLKM GOTO"
            )
        return

    new_tickers = [normalize_ticker(t) for t in args]

    for ticker in new_tickers:
        if ticker not in chat_watchlist:
            chat_watchlist.append(ticker)

    watchlist[chat_id] = chat_watchlist
    save_watchlist(watchlist)

    log(f"Chat {chat_id}: Added {new_tickers}")

    await update.message.reply_text(
        f"✅ Added {len(new_tickers)} ticker(s)\n\n"
        f"📊 Your watchlist ({len(chat_watchlist)}):\n{', '.join(chat_watchlist)}"
    )


async def cmd_unwl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unwl command - remove tickers"""
    chat_id = str(update.effective_chat.id)
    args = context.args

    if not args:
        await update.message.reply_text(
            "❌ Please specify tickers to remove.\n\n"
            "Example: /unwl BBRI TLKM"
        )
        return

    watchlist = load_watchlist()
    chat_watchlist = watchlist.get(chat_id, [])

    remove_tickers = [normalize_ticker(t) for t in args]
    removed_count = 0

    for ticker in remove_tickers:
        if ticker in chat_watchlist:
            chat_watchlist.remove(ticker)
            removed_count += 1

    watchlist[chat_id] = chat_watchlist
    save_watchlist(watchlist)

    log(f"Chat {chat_id}: Removed {remove_tickers}")

    if removed_count > 0:
        if chat_watchlist:
            await update.message.reply_text(
                f"✅ Removed {removed_count} ticker(s)\n\n"
                f"📊 Your watchlist ({len(chat_watchlist)}):\n{', '.join(chat_watchlist)}"
            )
        else:
            await update.message.reply_text(
                "✅ Removed all tickers\n\n"
                "📊 Your watchlist is now empty"
            )
    else:
        await update.message.reply_text(
            "⚠️ None of the specified tickers were in your watchlist"
        )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start and /help commands"""
    help_text = """
🤖 <b>Indonesian Stock Watchlist Bot</b>

<b>Commands:</b>

/wl - Show your watchlist
/wl BBRI TLKM GOTO - Add tickers
/unwl BBRI TLKM - Remove tickers
/help - Show this help

<b>Features:</b>
• Bad news monitoring for watchlist tickers
• Volume spike detection
• Price/volume pattern alerts

<b>Note:</b> Tickers are automatically formatted with .JK suffix
"""
    await update.message.reply_html(help_text)


async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown commands"""
    await update.message.reply_text(
        "❓ Unknown command.\n\n"
        "Use /help to see available commands."
    )


def main():
    """Main bot loop"""
    if not TELEGRAM_BOT_TOKEN:
        log("❌ TELEGRAM_BOT_TOKEN not configured in .env")
        return

    log("🤖 Starting Indonesian Stock Watchlist Bot...")

    try:
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

        application.add_handler(CommandHandler("start", cmd_help))
        application.add_handler(CommandHandler("help", cmd_help))
        application.add_handler(CommandHandler("wl", cmd_wl))
        application.add_handler(CommandHandler("unwl", cmd_unwl))
        application.add_handler(MessageHandler(filters.COMMAND, handle_unknown))

        log("✓ Bot handlers registered")
        log("✓ Bot is running... Press Ctrl+C to stop")

        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )

    except KeyboardInterrupt:
        log("⏸️  Bot stopped by user")
    except Exception as e:
        log(f"❌ Bot error: {e}")
        time.sleep(10)
        main()


if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            log(f"❌ Fatal error: {e}")
            log("⏳ Restarting in 30 seconds...")
            time.sleep(30)
