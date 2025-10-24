#!/usr/bin/env python3
"""Generate secure Telegram bot secret token."""

import secrets
import sys

def generate_telegram_secret():
    """Generate a secure random secret token for Telegram bot."""
    return secrets.token_urlsafe(32)

if __name__ == "__main__":
    secret = generate_telegram_secret()
    print(f"TELEGRAM_BOT_SECRET_TOKEN={secret}")
    print(f"\nAdd this to your .env file:")
    print(f"TELEGRAM_BOT_SECRET_TOKEN={secret}")
    print(f"\nAnd configure it in your Telegram bot via BotFather:")
    print(f"1. Send /setdomain to @BotFather")
    print(f"2. Select your bot")
    print(f"3. Set domain: {sys.argv[1] if len(sys.argv) > 1 else 'your-domain.com'}")
    print(f"4. Set secret token: {secret}")
