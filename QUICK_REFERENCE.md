# Quick Reference Guide - Dating Mini App

## 🎯 What Works Right Now

### User Journey
1. `/start` → Bot shows WebApp button
2. Click button → Mini App opens
3. Fill profile form (name, age, gender, etc.)
4. Submit → **Profile saved to database** ✅
5. Bot confirms → "✅ Профиль создан!"

### Key Features
- ✅ Profile creation with validation
- ✅ Age verification (18+)
- ✅ Location with privacy (geohash)
- ✅ Photo upload (3 photos)
- ✅ Database storage (PostgreSQL)
- ✅ Bot confirmation messages

---

## 📁 Key Files

### WebApp (Frontend)
- `webapp/index.html` - Profile form UI
- `webapp/js/app.js` - Form handling, validation, sends data to bot
- `webapp/css/style.css` - Styling

### Bot (Backend)
- `bot/main.py` - Main bot, handles WebApp data, saves to DB
- `bot/repository.py` - Database operations (CRUD)
- `bot/validation.py` - Profile validation logic
- `bot/geo.py` - Location processing, geohash
- `bot/db.py` - SQLAlchemy models (User, Profile, Photo)

### Database
- `migrations/versions/001_create_profile_tables.py` - DB schema

### Documentation
- `README.md` - Project overview
- `PROJECT_STATUS.md` - What's done vs. planned
- `PROFILE_CREATION_FLOW.md` - Detailed technical flow
- `SPEC.md` - Complete specification (future features)

---

## 🔧 Common Tasks

### Run Tests
```bash
pytest tests/ -v
# 111 tests, should all pass
```

### Check Database
```bash
# Connect to PostgreSQL
psql -U dating dating

# View profiles
SELECT * FROM profiles;

# View users
SELECT * FROM users;
```

### Run Bot Locally
```bash
# Set environment variables
export BOT_TOKEN="your_token"
export BOT_DATABASE_URL="postgresql+asyncpg://user:pass@host/db"
export WEBAPP_URL="https://your-domain.com"

# Run bot
python -m bot.main
```

### Run with Docker
```bash
# Development
docker compose -f docker-compose.dev.yml up

# Production
docker compose up -d
```

---

## 🐛 Debugging

### Profile not saving?
1. Check bot logs for errors
2. Verify `BOT_DATABASE_URL` is set
3. Check WebApp console for `tg.sendData()` call
4. Verify database connection: `docker compose logs db`

### WebApp not opening?
1. Check `WEBAPP_URL` is set correctly
2. Verify HTTPS (required for WebApp)
3. Check Traefik logs: `docker compose logs traefik`

### Validation errors?
Check `bot/validation.py` for requirements:
- Name: 2-100 chars
- Age: Must be 18+
- Gender: male/female/other
- Orientation: male/female/any
- Goal: friendship/dating/relationship/serious/casual/networking

---

## 📊 Database Schema

### Users Table
```sql
id              SERIAL PRIMARY KEY
tg_id           BIGINT UNIQUE       -- Telegram user ID
username        VARCHAR(255)
first_name      VARCHAR(255)
language_code   VARCHAR(10)
is_premium      BOOLEAN
is_banned       BOOLEAN
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

### Profiles Table
```sql
id              SERIAL PRIMARY KEY
user_id         INTEGER UNIQUE      -- FK to users.id
name            VARCHAR(100)
birth_date      DATE
gender          VARCHAR(20)         -- male/female/other
orientation     VARCHAR(20)         -- male/female/any
goal            VARCHAR(50)
bio             TEXT
city            VARCHAR(100)
geohash         VARCHAR(20)         -- ~5km precision
latitude        FLOAT
longitude       FLOAT
is_complete     BOOLEAN
created_at      TIMESTAMP
```

---

## 🚀 Next Steps to Implement

### High Priority
1. **View Profile** - `/profile` command
2. **Edit Profile** - Update existing profile
3. **Photo Storage** - Save actual image files

### Medium Priority
1. **Discovery** - Card stack to view other profiles
2. **Matching** - Like/pass actions, detect mutual likes
3. **Match Notifications** - Alert on matches

### Future
1. **Chat** - Real-time messaging (WebSocket)
2. **Payments** - Telegram Stars integration
3. **Moderation** - Report/block users

See `PROJECT_STATUS.md` for complete roadmap.

---

## 💡 Code Examples

### Send Data from WebApp
```javascript
// In webapp/js/app.js
const payload = {
  action: 'create_profile',
  profile: {
    name: "Alice",
    birth_date: "1995-06-15",
    gender: "female",
    // ... more fields
  }
};
tg.sendData(JSON.stringify(payload));
```

### Handle in Bot
```python
# In bot/main.py
@router.message(lambda m: m.web_app_data is not None)
async def handle_webapp_data(message: Message):
    data = json.loads(message.web_app_data.data)
    if data['action'] == 'create_profile':
        await handle_create_profile(message, data, ...)
```

### Validate Profile
```python
# In bot/validation.py
from bot.validation import validate_profile_data

is_valid, error = validate_profile_data(profile_data)
if not is_valid:
    print(f"Error: {error}")
```

### Query Database
```python
# In bot/repository.py
repository = ProfileRepository(session)
user = await repository.get_user_by_tg_id(123456)
profile = await repository.get_profile_by_user_id(user.id)
```

---

## 🔐 Environment Variables

### Required
```bash
BOT_TOKEN=123456789:ABCdef...           # From @BotFather
BOT_DATABASE_URL=postgresql+asyncpg://... # PostgreSQL connection
WEBAPP_URL=https://your-domain.com      # WebApp URL
```

### Optional
```bash
DOMAIN=your-domain.com                  # For HTTPS
ACME_EMAIL=admin@example.com           # For Let's Encrypt
POSTGRES_USER=dating                    # Database user
POSTGRES_PASSWORD=secret                # Database password
POSTGRES_DB=dating                      # Database name
```

See `.env.example` for complete list.

---

## 📞 Getting Help

- **Documentation**: See `docs/` directory
- **Issues**: [GitHub Issues](https://github.com/erliona/dating/issues)
- **Tests**: Run `pytest tests/ -v` for examples

---

## ✅ Pre-flight Checklist

Before deploying:
- [ ] All tests pass: `pytest tests/`
- [ ] Environment variables set
- [ ] Database migrations run: `alembic upgrade head`
- [ ] HTTPS configured (for WebApp)
- [ ] Bot token valid
- [ ] WebApp accessible

---

## 🎓 Learning Resources

### Telegram Bot API
- [Bot API Docs](https://core.telegram.org/bots/api)
- [WebApp Docs](https://core.telegram.org/bots/webapps)

### Technologies
- [aiogram](https://docs.aiogram.dev/) - Async Telegram bot framework
- [SQLAlchemy](https://docs.sqlalchemy.org/) - Database ORM
- [Alembic](https://alembic.sqlalchemy.org/) - Database migrations
- [PostgreSQL](https://www.postgresql.org/docs/) - Database

---

**Last Updated**: 2024-10-02
**Status**: Profile creation bug fixed ✅
