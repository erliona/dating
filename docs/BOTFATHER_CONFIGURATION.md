# BotFather Configuration Guide

## Overview

This guide explains how to configure your Telegram bot to work with the Dating Mini App, including the correct URL settings in BotFather.

## Issue #2: What URL to use in BotFather?

When configuring your bot with [@BotFather](https://t.me/BotFather), you need to specify the correct URL for your Mini App.

### Required Configuration

#### 1. Set WEBAPP_URL Environment Variable

In your `.env` file:

```bash
# For production (HTTPS required)
WEBAPP_URL=https://your-domain.com

# For local development (HTTP allowed for localhost only)
WEBAPP_URL=http://localhost:8080
```

**Important Notes:**
- Production deployments MUST use HTTPS
- Only `localhost` and `127.0.0.1` can use HTTP (for development)
- The URL should point to where your webapp is hosted
- Do NOT include trailing slashes

#### 2. Configure BotFather

Send the following commands to [@BotFather](https://t.me/BotFather):

1. **Set the Mini App URL** (NOT the Web App URL):
   ```
   /mybots
   → Select your bot
   → Bot Settings
   → Menu Button
   → Configure Menu Button
   → Send the URL: https://your-domain.com
   ```

2. **Alternative: Use Web App in Inline Mode** (optional):
   ```
   /setinlinemode
   → Select your bot
   → Send: Enable
   ```

### URL Configuration Examples

#### Production Setup

```bash
# .env file
WEBAPP_URL=https://dating.example.com
DOMAIN=dating.example.com
```

BotFather setting:
```
Menu Button URL: https://dating.example.com
```

#### Local Development

```bash
# .env file
WEBAPP_URL=http://localhost:8080
```

BotFather setting:
```
Menu Button URL: http://localhost:8080
# Note: This only works for testing with ngrok or similar tunneling
```

#### Using ngrok for Local Testing

If you want to test locally with BotFather:

1. Install and run ngrok:
   ```bash
   ngrok http 8080
   ```

2. Use the ngrok HTTPS URL:
   ```bash
   # .env file
   WEBAPP_URL=https://abcd1234.ngrok.io
   ```

3. Configure BotFather with the same ngrok URL:
   ```
   Menu Button URL: https://abcd1234.ngrok.io
   ```

### Verification

After configuration, test the setup:

1. Open your bot in Telegram
2. You should see a keyboard button with text "🚀 Открыть Mini App"
3. Clicking it should open your web app
4. The app should load and display the welcome screen

### Common Issues

#### Issue: "WebApp is not configured"

**Cause:** `WEBAPP_URL` environment variable is not set or is empty.

**Solution:** Set `WEBAPP_URL` in your `.env` file and restart the bot:
```bash
docker compose restart bot
```

#### Issue: "Invalid URL" error in BotFather

**Cause:** URL format is incorrect or doesn't use HTTPS in production.

**Solution:** Ensure URL:
- Starts with `https://` (production)
- Has no trailing slash
- Is accessible from the internet
- Has valid SSL certificate (production)

#### Issue: WebApp opens but immediately closes

**Cause:** This is EXPECTED behavior after profile submission. When `tg.sendData()` is called, Telegram automatically closes the WebApp.

**Solution:** This is normal - see "WebApp Closing Behavior" section below.

## WebApp Closing Behavior (Issue #1)

### Expected Behavior

When a user creates a profile:

1. User fills out the profile form
2. User clicks "Создать анкету" (Create Profile)
3. JavaScript calls `tg.sendData(JSON.stringify(payload))`
4. **WebApp automatically closes** ✅ This is expected!
5. User returns to the Telegram chat
6. Bot receives the data and processes it
7. Bot sends a confirmation message

### Why Does It Close?

According to the [Telegram Bot API documentation](https://core.telegram.org/bots/webapps#receiving-data-from-mini-apps):

> When the user presses the button that closes the Mini App and returns to the chat, the data is sent to the bot.

This is the standard behavior for Telegram Mini Apps when using `KeyboardButton` with `web_app` parameter (which is required to send data back to the bot).

### Alternative Flows

If you want the user to stay in the app after profile creation:

1. **Option A**: Don't use `tg.sendData()` - instead use HTTP API only
   - Pro: App doesn't close
   - Con: Need to handle authentication differently
   
2. **Option B**: Show success screen before calling `tg.sendData()`
   - Pro: User sees confirmation before closing
   - Con: Adds extra step

3. **Option C**: Use inline keyboard (current approach)
   - Pro: Standard Telegram behavior
   - Con: App closes after sending data

**Current Implementation:** We use Option C, which follows Telegram's recommended approach.

## Related Documentation

- [Telegram Bot API: WebApp](https://core.telegram.org/bots/webapps)
- [Telegram Bot API: KeyboardButton with WebApp](https://core.telegram.org/bots/webapps#keyboard-button-mini-apps)
- [Telegram Bot API: Receiving Data](https://core.telegram.org/bots/webapps#receiving-data-from-mini-apps)
- [BUGFIX_WEBAPP_DATA.md](archive/BUGFIX_WEBAPP_DATA.md) - Details on KeyboardButton vs InlineKeyboardButton

## Testing Checklist

- [ ] `.env` file has `WEBAPP_URL` set correctly
- [ ] Bot restarts successfully with no configuration errors
- [ ] BotFather Menu Button URL is configured
- [ ] `/start` command shows keyboard with "🚀 Открыть Mini App" button
- [ ] Clicking button opens the webapp
- [ ] Webapp loads and shows welcome screen
- [ ] Profile creation works and data is saved to database
- [ ] Bot sends confirmation message after profile creation
- [ ] WebApp closes after sending data (expected behavior)

## Support

If you encounter issues not covered in this guide:

1. Check the logs: `docker compose logs bot`
2. Verify environment variables: `docker compose config`
3. Test the webapp URL directly in a browser
4. Check the database: `docker compose exec postgres psql -U dating -d dating -c "SELECT * FROM users;"`

## Version

Document version: 1.3.0  
Last updated: 2024-10-03
