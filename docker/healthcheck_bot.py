#!/usr/bin/env python3
"""Healthcheck script for Telegram bot.

This script checks the health of the bot by checking the local HTTP API endpoint.
If the HTTP endpoint is not available, it falls back to checking Telegram API directly.
"""

import json
import os
import sys
import urllib.error
import urllib.request


def check_http_health() -> bool:
    """Check if bot's HTTP API is healthy.

    Returns:
        True if HTTP API is healthy, False otherwise.
    """
    # Check local HTTP API health endpoint
    api_port = int(os.getenv("API_PORT", "8080"))
    url = f"http://localhost:{api_port}/health"

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))

            if data.get("status") == "ok":
                print(f"Bot HTTP API is healthy on port {api_port}")
                return True
            else:
                print(
                    f"ERROR: HTTP API returned unexpected status: {data}",
                    file=sys.stderr,
                )
                return False

    except urllib.error.HTTPError as e:
        print(
            f"WARNING: HTTP error from local API: {e.code} {e.reason}", file=sys.stderr
        )
        return False
    except urllib.error.URLError as e:
        print(f"WARNING: Failed to connect to local API: {e.reason}", file=sys.stderr)
        return False
    except json.JSONDecodeError as e:
        print(f"WARNING: Invalid JSON response from local API: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"WARNING: Unexpected error checking local API: {e}", file=sys.stderr)
        return False


def check_telegram_api_health() -> bool:
    """Check if Telegram bot is healthy using getMe API.

    This is a fallback method when HTTP API is not available.

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
            data = json.loads(response.read().decode("utf-8"))

            # Check if request was successful
            if data.get("ok"):
                bot_info = data.get("result", {})
                username = bot_info.get("username", "unknown")
                print(f"Bot is healthy (via Telegram API): @{username}")
                return True
            else:
                print(f"ERROR: Telegram API returned not ok: {data}", file=sys.stderr)
                return False

    except urllib.error.HTTPError as e:
        print(
            f"ERROR: HTTP error from Telegram API: {e.code} {e.reason}", file=sys.stderr
        )
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


def check_bot_health() -> bool:
    """Check bot health using local HTTP API first, with Telegram API as fallback.

    Returns:
        True if bot is healthy, False otherwise.
    """
    # Try HTTP API first (faster and more reliable)
    if check_http_health():
        return True

    # Fall back to Telegram API if HTTP is not available
    print(
        "Local HTTP API not available, falling back to Telegram API check",
        file=sys.stderr,
    )
    return check_telegram_api_health()


if __name__ == "__main__":
    if check_bot_health():
        sys.exit(0)
    else:
        sys.exit(1)
