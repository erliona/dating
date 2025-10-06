# Bot Architecture Change: From Mini App Host to Notification Server

## Visual Comparison

### Before: Bot with Mini App

```
┌─────────────────────────────────────────────────────────────┐
│                         USER                                │
└───────────┬─────────────────────────────────────────────────┘
            │
            │ Opens Telegram
            ↓
┌─────────────────────────────────────────────────────────────┐
│                    TELEGRAM BOT                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Commands:                                           │   │
│  │  • /start  → Shows WebApp button                    │   │
│  │  • /notifications → Settings info                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  HTTP API Server (bot/api.py)                       │   │
│  │  • /api/profile/check                               │   │
│  │  • /api/profile                                      │   │
│  │  • /api/discover                                     │   │
│  │  • /api/like, /api/pass                             │   │
│  │  • /api/matches                                      │   │
│  │  • /api/favorites                                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↓                                   │
│                   Uses WebApp Button                         │
└──────────────────────────┬───────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                     MINI APP (WebApp)                        │
│  Calls bot/api.py endpoints for user interactions           │
└───────────────────────────┬──────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     API GATEWAY                              │
└───────────────────────────┬──────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  MICROSERVICES                               │
│  Profile • Discovery • Media • Chat • Auth                   │
└──────────────────────────────────────────────────────────────┘
```

### After: Notification-Only Bot

```
┌─────────────────────────────────────────────────────────────┐
│                         USER                                │
└───────┬────────────────────────────────────────┬─────────────┘
        │                                        ↑
        │ Opens WebApp directly                  │ Push Notifications
        │ (bot info / link)                      │
        ↓                                        │
┌─────────────────────────────────────────────────────────────┐
│                  MINI APP (WebApp)                           │
│  Direct communication with API Gateway                       │
│  No interaction with bot                                     │
└───────────────────────────┬──────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     API GATEWAY                              │
└────┬───────────────────────────────────────────┬─────────────┘
     ↓                                            ↓
┌─────────────────────────────────┐  ┌──────────────────────────┐
│       MICROSERVICES             │  │  NOTIFICATION SERVICE    │
│  Profile • Discovery            │  │  Routes notifications    │
│  Media • Chat • Auth            │  │  to bot                  │
└─────────────────────────────────┘  └────────┬─────────────────┘
                                              ↓
                                   ┌──────────────────────────┐
                                   │    TELEGRAM BOT          │
                                   │  (Notification Server)   │
                                   │                          │
                                   │  HTTP Endpoints:         │
                                   │  • POST /notifications/  │
                                   │    match                 │
                                   │  • POST /notifications/  │
                                   │    message               │
                                   │  • POST /notifications/  │
                                   │    like                  │
                                   │  • GET /health           │
                                   │                          │
                                   │  No commands!            │
                                   │  No WebApp button!       │
                                   └────────┬─────────────────┘
                                            ↓
                                   ┌──────────────────────────┐
                                   │    TELEGRAM API          │
                                   │  send_message()          │
                                   └────────┬─────────────────┘
                                            ↓
                                      User receives push
                                      notification
```

## Key Differences

| Aspect | Before | After |
|--------|--------|-------|
| **User Entry Point** | /start command in bot | Direct WebApp link |
| **Bot Commands** | /start, /notifications | None |
| **Bot HTTP Server** | Full API (bot/api.py) | Only notification endpoints |
| **WebApp ↔ Bot** | WebApp calls bot/api.py | No communication |
| **WebApp ↔ Services** | Via bot → API Gateway | Direct to API Gateway |
| **Notification Flow** | Services → Bot (internal) | Services → Notification Service → Bot |
| **Bot Dependencies** | API Gateway, WebApp URL | Only Telegram API |
| **Bot Responsibility** | Commands + API + Notifications | Only notifications |

## Message Flow Examples

### Before: User Likes Someone

```
User clicks Like in WebApp
  ↓
POST /api/like to bot/api.py
  ↓
bot/api.py → API Gateway
  ↓
API Gateway → Discovery Service
  ↓
Discovery Service creates interaction
  ↓
If match: Discovery Service calls bot notification function
  ↓
Bot sends Telegram notification to both users
```

### After: User Likes Someone

```
User clicks Like in WebApp
  ↓
POST /api/discovery/interactions to API Gateway (directly)
  ↓
API Gateway → Discovery Service
  ↓
Discovery Service creates interaction
  ↓
If match: Discovery Service → Notification Service
  ↓
Notification Service → POST /notifications/match to Bot
  ↓
Bot → Telegram API → Push notification to both users
```

## Benefits Visualization

```
                    SEPARATION OF CONCERNS
                    
┌────────────────────┐     ┌────────────────────┐     ┌────────────────────┐
│     MINI APP       │     │  MICROSERVICES     │     │   TELEGRAM BOT     │
│                    │     │                    │     │                    │
│  • User Interface  │     │  • Business Logic  │     │  • Notifications   │
│  • User Actions    │     │  • Data Storage    │     │  • Push Messages   │
│  • Input Forms     │     │  • API Endpoints   │     │                    │
│                    │     │                    │     │  Simple & Focused  │
│  Rich & Complex    │     │  Scalable          │     │                    │
└────────────────────┘     └────────────────────┘     └────────────────────┘
         ↓                          ↓                          ↑
    API Gateway              Process & Store            Notification Service
```

## Code Reduction

### bot/main.py

**Removed:**
- `start_handler()` - 30 lines
- `toggle_notifications()` - 20 lines
- `router` setup - 5 lines
- WebApp imports - 3 lines
- API server integration - 40 lines

**Added:**
- HTTP notification endpoints - 90 lines
- `create_notification_app()` - 10 lines
- `run_notification_server()` - 20 lines

**Net:** Cleaner, more focused code

### bot/config.py

**Changed:**
- Made `API_GATEWAY_URL` optional
- Made `WEBAPP_URL` optional
- Simplified validation logic

**Result:** More flexible configuration

## Deployment Changes

### Before

```yaml
telegram-bot:
  environment:
    BOT_TOKEN: ${BOT_TOKEN}
    API_GATEWAY_URL: http://api-gateway:8080  # Required
    WEBAPP_URL: ${WEBAPP_URL}                 # Required
    API_HOST: 0.0.0.0
    API_PORT: 8080
  depends_on:
    - api-gateway                              # Hard dependency
```

### After

```yaml
telegram-bot:
  environment:
    BOT_TOKEN: ${BOT_TOKEN}                   # Only required var!
    API_HOST: 0.0.0.0                         # Optional
    API_PORT: 8080                            # Optional
  # No dependencies! Can start independently
```

## Scalability Improvements

### Before: Coupled Scaling

```
More users → More WebApp requests → bot/api.py load ↑
          → Need to scale bot
          → But bot also handles notifications
          → Everything scales together
```

### After: Independent Scaling

```
More users → More WebApp requests → API Gateway load ↑
          → Scale API Gateway & Microservices

More notifications → Notification Service load ↑
                  → Scale Notification Service
                  
Bot scaling independent of user activity
```

## Summary

The refactoring transforms the bot from a **multi-purpose application server** to a **dedicated notification delivery service**, achieving:

✅ **Simpler architecture** - Single responsibility principle  
✅ **Better separation** - UI, business logic, and notifications are independent  
✅ **Easier maintenance** - Each component can be updated independently  
✅ **Independent scaling** - Scale based on actual usage patterns  
✅ **Reduced complexity** - Bot only knows about Telegram API  
✅ **More robust** - Fewer failure points, clearer error boundaries  

---

**See also:** `BOT_NOTIFICATION_REFACTORING.md` for complete technical documentation
