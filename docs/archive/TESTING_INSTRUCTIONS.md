# Manual Testing Instructions for WebApp Fix

## Prerequisites
- A working Telegram bot token
- A deployed or locally accessible WebApp (WEBAPP_URL configured)
- Access to the bot's logs

## Testing Steps

### 1. Start the Bot
```bash
export BOT_TOKEN="your_bot_token"
export BOT_DATABASE_URL="postgresql+asyncpg://user:password@localhost/dating"
export WEBAPP_URL="https://your-webapp-url.com"  # or http://localhost:8000 for local testing

python -m bot.main
```

Expected log output:
```
Starting bot with log level: INFO
Database connection successful
Starting polling
Start polling
Run polling for bot @your_bot_name id=... - 'Your Bot Name'
```

### 2. Send /start Command to the Bot

1. Open Telegram and find your bot
2. Send the `/start` command

**What You Should See:**
- A reply keyboard button appears at the bottom of the chat with text "Открыть мини-приложение"
- The button should be visible in the keyboard area (not as an inline button above the message)

**Expected Bot Logs:**
```
INFO - Start command received from user_id=123456, username=your_username
DEBUG - Config loaded successfully
DEBUG - Sending webapp button to user_id=123456 with url=https://...
```

### 3. Open the WebApp

1. Click the "Открыть мини-приложение" button
2. The WebApp should open in full screen

**What You Should See:**
- The profile creation form loads
- All form fields are visible and editable

### 4. Fill Out the Profile Form

Fill in the required fields:
- **Имя** (Name): Enter your name (e.g., "Алиса")
- **Возраст** (Age): Enter your age (18+)
- **Пол** (Gender): Select your gender
- **Кого ищешь** (Preference): Select preference

Optionally fill in:
- О себе (Bio)
- Город или регион (Location)
- Интересы (Interests)
- Цель знакомства (Goal)
- Фото (Photo URL)

### 5. Submit the Form

1. Click "Отправить" (Submit) button
2. The WebApp should close automatically

**Expected Bot Logs (THIS IS THE KEY TEST):**
```
INFO - WebApp data received from user_id=123456
INFO - Parsed payload from user_id=123456, action=create_profile
INFO - Processing profile data from user_id=123456
DEBUG - Profile built successfully: Profile(user_id=123456, name='Алиса', ...)
INFO - Finalizing profile for user_id=123456
DEBUG - Profile exists: False for user_id=123456
INFO - Profile upserted successfully for user_id=123456
INFO - Profile save completed for user_id=123456
DEBUG - No matches found for user_id=123456
```

**What You Should See in Telegram:**
- Bot sends a confirmation message: "Спасибо! Как только мы найдём подходящую пару, я сразу дам знать."

### 6. Verify Database

Check the database to confirm the profile was saved:

```sql
SELECT * FROM profiles WHERE user_id = 123456;
```

You should see:
- A record with the user_id
- All the profile data you entered

## Troubleshooting

### If Logs Don't Show "WebApp data received"

This indicates the WebApp button is not configured correctly. Verify:
1. The button is a `KeyboardButton` (ReplyKeyboard), not an `InlineKeyboardButton`
2. The `web_app` parameter is set with a valid WebAppInfo URL
3. The WebApp is properly calling `tg.sendData(JSON.stringify(payload))`

### If WebApp Doesn't Open

Check:
1. WEBAPP_URL is configured and accessible
2. The URL uses HTTPS (or HTTP for localhost)
3. The WebApp HTML includes the Telegram WebApp script: `<script src="https://telegram.org/js/telegram-web-app.js"></script>`

### If Form Validation Fails

Check:
1. All required fields are filled (name, age, gender, preference)
2. Age is 18 or greater
3. Name contains only letters, spaces, and hyphens
4. Photo URL (if provided) uses HTTPS

## Expected Results After Fix

✅ **Before the fix:**
- No "WebApp data received" logs
- Database remains empty
- No confirmation message from bot

✅ **After the fix:**
- "WebApp data received" logs appear
- Profile is saved to database
- User receives confirmation message

## Debug Command

You can also use the `/debug` command to check the bot's status:
```
/debug
```

This will show:
- Bot information
- Configuration (with masked sensitive data)
- Database connection status
- Database statistics (number of profiles, interactions, matches)
- System information
