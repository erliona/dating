#!/usr/bin/env python3
"""Healthcheck script for Telegram bot using getMe API."""

import os
import sys
import urllib.request
import urllib.error
import json


def check_bot_health() -> bool:
    """Check if Telegram bot is healthy using getMe API.
    
    Returns:
        True if bot is healthy, False otherwise.
    """
    bot_token = os.getenv("BOT_TOKEN")
    
    if not bot_token:
        print("ERROR: BOT_TOKEN not set", file=sys.stderr)
        return False
    
    # Telegram Bot API getMe endpoint
    url = f"https://api.telegram.org/bot{bot_token}/getMe"
    
    try:
        # Make request to Telegram API with 10 second timeout
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            # Check if request was successful
            if data.get("ok"):
                bot_info = data.get("result", {})
                username = bot_info.get("username", "unknown")
                print(f"Bot is healthy: @{username}")
                return True
            else:
                print(f"ERROR: Telegram API returned not ok: {data}", file=sys.stderr)
                return False
                
    except urllib.error.HTTPError as e:
        print(f"ERROR: HTTP error from Telegram API: {e.code} {e.reason}", file=sys.stderr)
        return False
    except urllib.error.URLError as e:
        print(f"ERROR: Failed to connect to Telegram API: {e.reason}", file=sys.stderr)
        return False
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON response from Telegram API: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    if check_bot_health():
        sys.exit(0)
    else:
        sys.exit(1)
