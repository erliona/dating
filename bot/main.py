"""Entry point for the dating Telegram bot."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import platform
import sys
from dataclasses import dataclass, field
from typing import Any, Optional

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, Message, ReplyKeyboardMarkup,
                           ReplyKeyboardRemove, WebAppData, WebAppInfo)

from sqlalchemy import text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from .analytics import track_command, track_interaction, track_profile_action
from .config import BotConfig, load_config
from .db import (
    InteractionRepository,
    MatchRepository,
    ProfileRepository,
    UserSettingsRepository,
)
from .security import (
    RateLimiter,
    RateLimitConfig,
    sanitize_user_input,
    validate_profile_data,
)


LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class Profile:
    """User profile collected from the mini-app."""

    user_id: int
    name: str
    age: int
    gender: str
    preference: str
    bio: str | None = None
    location: str | None = None
    interests: list[str] = field(default_factory=list)
    goal: str | None = None
    photo_file_id: str | None = None
    photo_url: str | None = None




ROUTER = Router()

BOT_CONTEXT_STORAGE_ATTR = "_dating_bot_context"
CONFIG_CONTEXT_KEY = "config"
REPOSITORY_CONTEXT_KEY = "profile_repository"
SETTINGS_REPOSITORY_KEY = "settings_repository"
INTERACTION_REPOSITORY_KEY = "interaction_repository"
MATCH_REPOSITORY_KEY = "match_repository"
RATE_LIMITER_KEY = "rate_limiter"
ENGINE_CONTEXT_KEY = "engine"


def _set_bot_context_value(bot: Bot, key: str, value: Any) -> None:
    """Store arbitrary data inside the bot instance."""

    if hasattr(bot, "__setitem__"):
        try:
            bot[key] = value  # type: ignore[index]
            return
        except TypeError:
            pass

    context: Optional[dict[str, Any]] = getattr(bot, BOT_CONTEXT_STORAGE_ATTR, None)
    if context is None or not isinstance(context, dict):
        context = {}
        setattr(bot, BOT_CONTEXT_STORAGE_ATTR, context)
    context[key] = value


def _get_bot_context_value(bot: Bot, key: str) -> Any:
    """Retrieve a value from the bot context if available."""

    if hasattr(bot, "__getitem__"):
        try:
            return bot[key]  # type: ignore[index]
        except (KeyError, TypeError):
            pass

    context: Optional[dict[str, Any]] = getattr(bot, BOT_CONTEXT_STORAGE_ATTR, None)
    if isinstance(context, dict):
        return context.get(key)
    return None


def attach_bot_context(
    bot: Bot,
    config: BotConfig,
    repository: ProfileRepository,
    settings_repository: UserSettingsRepository,
    interaction_repository: InteractionRepository,
    match_repository: MatchRepository,
    rate_limiter: RateLimiter,
    engine: Any = None,
) -> None:
    """Populate the bot context with common application dependencies."""

    _set_bot_context_value(bot, CONFIG_CONTEXT_KEY, config)
    _set_bot_context_value(bot, REPOSITORY_CONTEXT_KEY, repository)
    _set_bot_context_value(bot, SETTINGS_REPOSITORY_KEY, settings_repository)
    _set_bot_context_value(bot, INTERACTION_REPOSITORY_KEY, interaction_repository)
    _set_bot_context_value(bot, MATCH_REPOSITORY_KEY, match_repository)
    _set_bot_context_value(bot, RATE_LIMITER_KEY, rate_limiter)
    if engine is not None:
        _set_bot_context_value(bot, ENGINE_CONTEXT_KEY, engine)


def get_config(bot: Bot | None) -> BotConfig:
    if bot is None:
        raise RuntimeError("Bot instance is not available")

    config = _get_bot_context_value(bot, CONFIG_CONTEXT_KEY)
    if not isinstance(config, BotConfig):
        raise RuntimeError("Bot configuration is not loaded")
    return config


def get_repository(bot: Bot | None) -> ProfileRepository:
    if bot is None:
        raise RuntimeError("Bot instance is not available")

    repository = _get_bot_context_value(bot, REPOSITORY_CONTEXT_KEY)
    if not isinstance(repository, ProfileRepository):
        raise RuntimeError("Profile repository is not initialized")
    return repository


def get_settings_repository(bot: Bot | None) -> UserSettingsRepository:
    if bot is None:
        raise RuntimeError("Bot instance is not available")

    repository = _get_bot_context_value(bot, SETTINGS_REPOSITORY_KEY)
    if not isinstance(repository, UserSettingsRepository):
        raise RuntimeError("Settings repository is not initialized")
    return repository


def get_interaction_repository(bot: Bot | None) -> InteractionRepository:
    if bot is None:
        raise RuntimeError("Bot instance is not available")

    repository = _get_bot_context_value(bot, INTERACTION_REPOSITORY_KEY)
    if not isinstance(repository, InteractionRepository):
        raise RuntimeError("Interaction repository is not initialized")
    return repository


def get_match_repository(bot: Bot | None) -> MatchRepository:
    if bot is None:
        raise RuntimeError("Bot instance is not available")

    repository = _get_bot_context_value(bot, MATCH_REPOSITORY_KEY)
    if not isinstance(repository, MatchRepository):
        raise RuntimeError("Match repository is not initialized")
    return repository


def get_rate_limiter(bot: Bot | None) -> RateLimiter:
    """Get the rate limiter from bot context."""
    if bot is None:
        raise RuntimeError("Bot instance is not available")

    rate_limiter = _get_bot_context_value(bot, RATE_LIMITER_KEY)
    if not isinstance(rate_limiter, RateLimiter):
        raise RuntimeError("Rate limiter is not initialized")
    return rate_limiter


def normalise_choice(value: str) -> str:
    normalised = value.strip().lower()
    if normalised in {"m", "male", "м", "муж", "мужчина"}:
        return "male"
    if normalised in {"f", "female", "ж", "жен", "женщина"}:
        return "female"
    if normalised in {"o", "other", "другой", "инт"}:
        return "other"
    if normalised in {"any", "a", "любой", "anyone"}:
        return "any"
    raise ValueError("Unexpected option provided")


GOAL_ALIASES: dict[str, set[str]] = {
    "serious": {
        "serious",
        "relationship",
        "relationships",
        "отношения",
        "серьезные",
        "серьёзные",
        "серьезные отношения",
        "серьёзные отношения",
        "долгие",
        "долгие отношения",
        "семью",
        "брак",
        "long_term",
    },
    "friendship": {
        "friendship",
        "friends",
        "дружба",
        "дружбу",
        "приятели",
        "дружеское общение",
        "найти друзей",
    },
    "networking": {
        "networking",
        "общение",
        "компания",
        "общаться",
        "нетворкинг",
        "пообщаться",
    },
    "casual": {
        "casual",
        "fun",
        "легкие",
        "лёгкие",
        "легкие встречи",
        "лёгкие встречи",
        "без обязательств",
        "casual_dating",
        "флирт",
    },
}

GOAL_TITLES: dict[str, str] = {
    "serious": "серьёзные отношения",
    "friendship": "дружбу",
    "networking": "общение",
    "casual": "лёгкие встречи",
}


def normalise_goal(value: str) -> str:
    normalised = value.strip().lower()
    if not normalised:
        raise ValueError("Empty goal value")
    for key, aliases in GOAL_ALIASES.items():
        if normalised == key or normalised in aliases:
            return key
    raise ValueError("Unexpected goal provided")


def build_profile_from_payload(user_id: int, payload: dict[str, object]) -> Profile:
    try:
        name = str(payload["name"]).strip()
        age = int(payload["age"])
        gender = normalise_choice(str(payload["gender"]))
        preference = normalise_choice(str(payload["preference"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Некорректные данные анкеты") from exc

    if not name:
        raise ValueError("Имя не может быть пустым.")
    if age < 18:
        raise ValueError("Возраст должен быть 18+.")

    bio = payload.get("bio")
    bio_text = str(bio).strip() if bio is not None else None
    if bio_text == "":
        bio_text = None

    location_raw = payload.get("location")
    location_text = str(location_raw).strip() if location_raw is not None else None
    if location_text == "":
        location_text = None

    interests_raw = payload.get("interests")
    interests: list[str] = []
    if isinstance(interests_raw, list):
        interests = [
            str(item).strip()
            for item in interests_raw
            if str(item).strip()
        ]
    elif isinstance(interests_raw, str):
        interests = [
            part.strip()
            for part in interests_raw.split(",")
            if part.strip()
        ]

    goal_raw = payload.get("goal")
    goal_value: str | None = None
    if goal_raw is not None:
        goal_candidate = str(goal_raw).strip()
        if goal_candidate:
            goal_value = normalise_goal(goal_candidate)

    photo_url_raw = payload.get("photo_url")
    photo_url = str(photo_url_raw).strip() if photo_url_raw is not None else None
    if photo_url == "":
        photo_url = None
    elif photo_url is not None:
        if not photo_url.startswith("https://"):
            raise ValueError("Ссылка на фото должна использовать HTTPS протокол.")

    return Profile(
        user_id=user_id,
        name=name,
        age=age,
        gender=gender,
        preference=preference,
        bio=bio_text,
        location=location_text,
        interests=interests,
        goal=goal_value,
        photo_url=photo_url,
    )


async def handle_interaction(message: Message, from_user_id: int, to_user_id: int, action: str) -> None:
    """Handle like/dislike interaction between users.
    
    Args:
        message: Message object from the user.
        from_user_id: User ID who initiated the interaction.
        to_user_id: User ID who is the target of the interaction.
        action: Type of interaction ('like' or 'dislike').
    """
    bot = message.bot
    LOGGER.info("Processing %s from user %s to user %s", action, from_user_id, to_user_id)
    
    try:
        interaction_repo = get_interaction_repository(bot)
        match_repo = get_match_repository(bot)
        profile_repo = get_repository(bot)
    except RuntimeError as exc:
        LOGGER.exception("Repositories unavailable: %s", exc)
        await message.answer("Произошла внутренняя ошибка. Попробуйте позже.")
        return
    
    # Create or update the interaction
    try:
        await interaction_repo.create(from_user_id, to_user_id, action)
        
        # Track the interaction
        track_interaction(action)
        
    except OperationalError as exc:
        LOGGER.error("Database connection error when saving interaction: %s", exc)
        await message.answer("Не удалось подключиться к базе данных. Попробуйте позже.")
        return
    except SQLAlchemyError as exc:
        LOGGER.exception("Database error when saving interaction: %s", exc)
        await message.answer("Не удалось сохранить действие. Попробуйте позже.")
        return
    except Exception as exc:
        # Catch any other unexpected errors
        LOGGER.exception("Unexpected error when saving interaction: %s", exc)
        await message.answer("Не удалось сохранить действие. Попробуйте позже.")
        return
    
    # If it's a like, check for mutual match
    if action == "like":
        is_mutual = await interaction_repo.check_mutual_like(from_user_id, to_user_id)
        
        if is_mutual:
            # Create match
            try:
                match = await match_repo.create(from_user_id, to_user_id)
                LOGGER.info("New match created: %s and %s", from_user_id, to_user_id)
                
                # Track the match
                track_interaction("match")
                
                # Get both profiles
                user_profile = await profile_repo.get(from_user_id)
                matched_profile = await profile_repo.get(to_user_id)
                
                if user_profile and matched_profile:
                    # Notify both users
                    await message.answer(
                        "🎉 У вас взаимная симпатия!\n\n" + _format_match_message(matched_profile),
                        reply_markup=ReplyKeyboardRemove(),
                    )
                    await _send_photo_reply(message, matched_profile)
                    
                    await bot.send_message(
                        chat_id=to_user_id,
                        text="🎉 У вас взаимная симпатия!\n\n" + _format_match_message(user_profile),
                        reply_markup=ReplyKeyboardRemove(),
                    )
                    await _send_profile_photo(bot, to_user_id, user_profile)
                else:
                    LOGGER.warning("Could not load profiles for match notification")
                    await message.answer("🎉 У вас взаимная симпатия!")
            except OperationalError as exc:
                LOGGER.error("Database connection error when creating match: %s", exc)
                await message.answer("🎉 У вас взаимная симпатия!")
            except SQLAlchemyError as exc:
                LOGGER.exception("Database error when creating match: %s", exc)
                await message.answer("🎉 У вас взаимная симпатия!")
            except Exception as exc:
                # Catch any other unexpected errors
                LOGGER.exception("Unexpected error when creating match: %s", exc)
                await message.answer("🎉 У вас взаимная симпатия!")
        else:
            # Like sent but no match yet
            await message.answer("✅ Симпатия отправлена!")
    else:
        # Dislike - just confirm
        await message.answer("👌 Понятно, продолжаем поиск!")


async def finalize_profile(message: Message, profile: Profile, is_update: bool = False) -> None:
    """Finalize and save a user profile, optionally searching for matches.
    
    Args:
        message: Message object from the user.
        profile: Profile object to save.
        is_update: Whether this is an update to an existing profile.
    """
    bot = message.bot
    LOGGER.info("Finalizing profile for user_id=%s", profile.user_id)
    
    try:
        repository = get_repository(bot)
    except RuntimeError as exc:
        LOGGER.exception("Profile repository is unavailable: %s", exc)
        await message.answer(
            "Не удалось сохранить анкету из-за внутренней ошибки. Попробуйте позже.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return
    
    # Check if profile exists before saving
    existing_profile = await repository.get(profile.user_id)
    is_existing = existing_profile is not None
    LOGGER.debug("Profile exists: %s for user_id=%s", is_existing, profile.user_id)

    try:
        await repository.upsert(profile)
        LOGGER.info("Profile upserted successfully for user_id=%s", profile.user_id)
        
        # Track profile action
        if is_existing:
            track_profile_action("update")
        else:
            track_profile_action("create")
    except OperationalError as exc:  # pragma: no cover - debug assistance
        LOGGER.error(
            "Database connection error while saving profile for user_id=%s: %s", profile.user_id, exc
        )
        await message.answer(
            "Не удалось подключиться к базе данных. Попробуйте позже.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return
    except SQLAlchemyError as exc:  # pragma: no cover - debug assistance
        LOGGER.exception(
            "Database error while saving profile for user_id=%s: %s", profile.user_id, exc
        )
        await message.answer(
            "Не удалось сохранить анкету. Попробуйте позже.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return
    except Exception as exc:  # pragma: no cover - debug assistance
        LOGGER.exception(
            "Unexpected error while saving profile for user_id=%s: %s", profile.user_id, exc
        )
        await message.answer(
            "Не удалось сохранить анкету. Попробуйте позже.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    LOGGER.info("Profile save completed for user_id=%s", profile.user_id)
    
    # If this was an update, just confirm
    if existing_profile:
        LOGGER.debug("Profile updated (not new) for user_id=%s", profile.user_id)
        await message.answer(
            "Профиль обновлён!",
            reply_markup=ReplyKeyboardRemove(),
        )
        return
    
    # For new profiles, look for matches
    LOGGER.info("Looking for matches for new profile user_id=%s", profile.user_id)
    match = await repository.find_mutual_match(profile)

    if match:
        LOGGER.info("Match found! user_id=%s matched with user_id=%s", 
                   profile.user_id, match.user_id)
        await message.answer(
            _format_match_message(match),
            reply_markup=ReplyKeyboardRemove(),
        )
        await _send_photo_reply(message, match)
        await bot.send_message(
            chat_id=match.user_id,
            text=_format_match_message(profile),
            reply_markup=ReplyKeyboardRemove(),
        )
        await _send_profile_photo(bot, match.user_id, profile)
    else:
        LOGGER.debug("No matches found for user_id=%s", profile.user_id)
        await message.answer(
            "Спасибо! Как только мы найдём подходящую пару, я сразу дам знать.",
            reply_markup=ReplyKeyboardRemove(),
        )


@ROUTER.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    """Handle the /start command."""
    
    track_command("start")
    
    LOGGER.info("Start command received from user_id=%s, username=%s", 
                message.from_user.id, message.from_user.username)

    try:
        config = get_config(message.bot)
        LOGGER.debug("Config loaded successfully")
    except RuntimeError as exc:
        LOGGER.exception("Bot configuration is unavailable: %s", exc)
        await message.answer(
            "Не удалось получить конфигурацию бота. Попробуйте написать позже.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return
    await state.clear()
    
    if not config.webapp_url:
        LOGGER.warning("WEBAPP_URL is not configured")
        await message.answer(
            "Привет! Для использования этого бота необходимо настроить мини-приложение.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return
    
    greeting = [
        "Привет! Я бот для знакомств.",
        "Открой мини-приложение, чтобы создать анкету или управлять профилем.",
    ]

    # Important: Use KeyboardButton (not InlineKeyboardButton) with web_app parameter
    # to enable data submission from the WebApp back to the bot via F.web_app_data filter.
    # InlineKeyboardButton with web_app only opens the app but doesn't send data back.
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="Открыть мини-приложение",
                    web_app=WebAppInfo(url=config.webapp_url),
                )
            ]
        ],
        resize_keyboard=True,
    )

    LOGGER.debug("Sending webapp button to user_id=%s with url=%s", 
                 message.from_user.id, config.webapp_url)
    await message.answer("\n".join(greeting), reply_markup=keyboard)


@ROUTER.message(Command(commands={"cancel", "reset"}))
async def cancel_handler(message: Message, state: FSMContext) -> None:
    """Allow users to cancel any ongoing state."""
    
    track_command("cancel")

    await state.clear()
    await message.answer(
        "Все операции отменены. Напиши /start, чтобы начать.",
        reply_markup=ReplyKeyboardRemove(),
    )


@ROUTER.message(Command(commands={"debug"}))
async def debug_handler(message: Message) -> None:
    """Show comprehensive debug information about the bot's status."""
    
    track_command("debug")
    
    LOGGER.info("Debug command received from user_id=%s", message.from_user.id)
    
    debug_lines = ["🔧 <b>Debug Information</b>\n"]
    
    # Bot Status
    debug_lines.append("📱 <b>Bot Status:</b>")
    try:
        bot_info = await message.bot.get_me()
        debug_lines.append(f"  ✅ Bot Running")
        debug_lines.append(f"  • ID: <code>{bot_info.id}</code>")
        debug_lines.append(f"  • Username: @{bot_info.username}")
        debug_lines.append(f"  • Name: {bot_info.first_name}")
    except Exception as exc:
        debug_lines.append(f"  ❌ Failed to get bot info: {exc}")
        LOGGER.exception("Failed to get bot info in debug handler")
    
    debug_lines.append("")
    
    # Configuration Status
    debug_lines.append("⚙️ <b>Configuration:</b>")
    try:
        config = get_config(message.bot)
        debug_lines.append(f"  ✅ Config Loaded")
        
        # Show webapp URL status
        if config.webapp_url:
            # Mask part of the URL for security
            webapp_display = config.webapp_url
            if len(webapp_display) > 50:
                webapp_display = webapp_display[:47] + "..."
            debug_lines.append(f"  • WebApp URL: {webapp_display}")
        else:
            debug_lines.append(f"  ⚠️ WebApp URL: Not configured")
        
        # Show database URL (masked)
        db_url_masked = config.database_url
        # Mask password in DB URL
        if "@" in db_url_masked and "://" in db_url_masked:
            parts = db_url_masked.split("://", 1)
            if len(parts) == 2:
                protocol, rest = parts
                if "@" in rest:
                    credentials, host_part = rest.rsplit("@", 1)
                    if ":" in credentials:
                        user, _ = credentials.split(":", 1)
                        db_url_masked = f"{protocol}://{user}:***@{host_part}"
        debug_lines.append(f"  • Database: {db_url_masked}")
        
    except RuntimeError as exc:
        debug_lines.append(f"  ❌ Config Error: {exc}")
        LOGGER.exception("Failed to get config in debug handler")
    
    debug_lines.append("")
    
    # Database Connection
    debug_lines.append("🗄️ <b>Database Connection:</b>")
    db_connected = False
    try:
        repository = get_repository(message.bot)
        # Try to execute a simple query to test connection
        test_profile = await repository.get(user_id=0)  # Non-existent user
        debug_lines.append(f"  ✅ Connected")
        db_connected = True
    except Exception as exc:
        debug_lines.append(f"  ❌ Connection Failed: {exc}")
        LOGGER.exception("Database connection test failed in debug handler")
    
    # Database Statistics (only if connected)
    if db_connected:
        debug_lines.append("")
        debug_lines.append("📊 <b>Database Statistics:</b>")
        
        try:
            # Get all repositories
            profile_repo = get_repository(message.bot)
            interaction_repo = get_interaction_repository(message.bot)
            match_repo = get_match_repository(message.bot)
            settings_repo = get_settings_repository(message.bot)
            
            # Count profiles using direct SQL
            from sqlalchemy import select, func as sql_func
            from .db import ProfileModel, UserInteractionModel, MatchModel, UserSettingsModel
            
            async with profile_repo._session_factory() as session:
                # Count profiles
                profile_count_result = await session.execute(
                    select(sql_func.count()).select_from(ProfileModel)
                )
                profile_count = profile_count_result.scalar() or 0
                
                # Count interactions
                interaction_count_result = await session.execute(
                    select(sql_func.count()).select_from(UserInteractionModel)
                )
                interaction_count = interaction_count_result.scalar() or 0
                
                # Count matches
                match_count_result = await session.execute(
                    select(sql_func.count()).select_from(MatchModel)
                )
                match_count = match_count_result.scalar() or 0
                
                # Count settings
                settings_count_result = await session.execute(
                    select(sql_func.count()).select_from(UserSettingsModel)
                )
                settings_count = settings_count_result.scalar() or 0
            
            debug_lines.append(f"  • Profiles: {profile_count}")
            debug_lines.append(f"  • Interactions: {interaction_count}")
            debug_lines.append(f"  • Matches: {match_count}")
            debug_lines.append(f"  • User Settings: {settings_count}")
            
        except Exception as exc:
            debug_lines.append(f"  ❌ Failed to get statistics: {exc}")
            LOGGER.exception("Failed to get database statistics in debug handler")
    
    debug_lines.append("")
    
    # Environment Variables
    debug_lines.append("🔐 <b>Environment Variables:</b>")
    env_vars = [
        ("BOT_TOKEN", "***" if os.getenv("BOT_TOKEN") else "Not set"),
        ("BOT_DATABASE_URL", "Set" if os.getenv("BOT_DATABASE_URL") else "Not set"),
        ("DATABASE_URL", "Set" if os.getenv("DATABASE_URL") else "Not set"),
        ("WEBAPP_URL", "Set" if os.getenv("WEBAPP_URL") else "Not set"),
        ("DEBUG", os.getenv("DEBUG", "Not set")),
    ]
    for var_name, var_status in env_vars:
        debug_lines.append(f"  • {var_name}: {var_status}")
    
    debug_lines.append("")
    
    # System Information
    debug_lines.append("💻 <b>System Information:</b>")
    import sys
    import platform
    import aiogram
    import sqlalchemy
    
    debug_lines.append(f"  • Python: {sys.version.split()[0]}")
    debug_lines.append(f"  • Platform: {platform.system()} {platform.release()}")
    debug_lines.append(f"  • Aiogram: {aiogram.__version__}")
    debug_lines.append(f"  • SQLAlchemy: {sqlalchemy.__version__}")
    
    # Log level
    current_log_level = logging.getLevelName(LOGGER.getEffectiveLevel())
    debug_lines.append(f"  • Log Level: {current_log_level}")
    
    # Send the debug info
    debug_message = "\n".join(debug_lines)
    await message.answer(debug_message, parse_mode=ParseMode.HTML)


@ROUTER.message(Command(commands={"matches"}))
async def matches_handler(message: Message) -> None:
    """Show user's match history."""
    
    track_command("matches")
    
    LOGGER.info("Matches command received from user_id=%s", message.from_user.id)
    user_id = message.from_user.id
    
    try:
        match_repo = get_match_repository(message.bot)
        profile_repo = get_repository(message.bot)
    except RuntimeError as exc:
        LOGGER.exception("Repositories are unavailable: %s", exc)
        await message.answer(
            "Не удалось получить данные о матчах. Попробуйте позже.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return
    
    try:
        # Get user's matches
        match_ids = await match_repo.get_matches(user_id)
        
        if not match_ids:
            await message.answer(
                "У вас пока нет матчей. 💔\n\nОткройте мини-приложение, чтобы начать знакомства!",
                reply_markup=ReplyKeyboardRemove(),
            )
            return
        
        # Build response with match info
        response_lines = [f"💑 <b>Ваши матчи ({len(match_ids)}):</b>\n"]
        
        for i, match_id in enumerate(match_ids, 1):
            try:
                match_profile = await profile_repo.get(match_id)
                if match_profile:
                    response_lines.append(
                        f"{i}. {match_profile.name}, {match_profile.age} лет"
                    )
                    if match_profile.location:
                        response_lines.append(f"   📍 {match_profile.location}")
                    if match_profile.interests:
                        interests_preview = ", ".join(match_profile.interests[:3])
                        if len(match_profile.interests) > 3:
                            interests_preview += "..."
                        response_lines.append(f"   ❤️ {interests_preview}")
                    response_lines.append("")  # Empty line between matches
            except Exception as exc:
                LOGGER.error("Failed to get profile for match %s: %s", match_id, exc)
                continue
        
        response_message = "\n".join(response_lines)
        await message.answer(response_message, parse_mode=ParseMode.HTML)
        
    except Exception as exc:
        LOGGER.exception("Error getting matches for user_id=%s: %s", user_id, exc)
        await message.answer(
            "Произошла ошибка при получении списка матчей. Попробуйте позже.",
            reply_markup=ReplyKeyboardRemove(),
        )


@ROUTER.message(Command(commands={"stats"}))
async def stats_handler(message: Message) -> None:
    """Show user's statistics and analytics."""
    
    track_command("stats")
    
    LOGGER.info("Stats command received from user_id=%s", message.from_user.id)
    user_id = message.from_user.id
    
    try:
        match_repo = get_match_repository(message.bot)
        profile_repo = get_repository(message.bot)
    except RuntimeError as exc:
        LOGGER.exception("Repositories are unavailable: %s", exc)
        await message.answer(
            "Не удалось получить статистику. Попробуйте позже.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return
    
    try:
        # Check if user has a profile
        user_profile = await profile_repo.get(user_id)
        if not user_profile:
            await message.answer(
                "У вас ещё нет анкеты. Откройте мини-приложение, чтобы создать профиль!",
                reply_markup=ReplyKeyboardRemove(),
            )
            return
        
        # Get user statistics
        stats = await match_repo.get_user_stats(user_id)
        
        # Calculate success rate
        total_interactions = stats["likes_sent"] + stats["dislikes_sent"]
        if total_interactions > 0:
            match_rate = (stats["matches_count"] / stats["likes_sent"] * 100) if stats["likes_sent"] > 0 else 0
        else:
            match_rate = 0
        
        # Build response
        response_lines = [
            "📊 <b>Ваша статистика:</b>\n",
            f"💑 <b>Матчи:</b> {stats['matches_count']}",
            f"❤️ <b>Отправлено симпатий:</b> {stats['likes_sent']}",
            f"💌 <b>Получено симпатий:</b> {stats['likes_received']}",
            f"👎 <b>Отправлено дизлайков:</b> {stats['dislikes_sent']}",
        ]
        
        if stats["likes_sent"] > 0:
            response_lines.append(f"\n📈 <b>Процент успеха:</b> {match_rate:.1f}%")
        
        # Add profile info
        response_lines.append(f"\n👤 <b>Ваш профиль:</b>")
        response_lines.append(f"  • Имя: {user_profile.name}")
        response_lines.append(f"  • Возраст: {user_profile.age} лет")
        if user_profile.location:
            response_lines.append(f"  • Локация: {user_profile.location}")
        if user_profile.interests:
            interests_text = ", ".join(user_profile.interests[:5])
            if len(user_profile.interests) > 5:
                interests_text += f" и ещё {len(user_profile.interests) - 5}"
            response_lines.append(f"  • Интересы: {interests_text}")
        
        response_message = "\n".join(response_lines)
        await message.answer(response_message, parse_mode=ParseMode.HTML)
        
    except Exception as exc:
        LOGGER.exception("Error getting stats for user_id=%s: %s", user_id, exc)
        await message.answer(
            "Произошла ошибка при получении статистики. Попробуйте позже.",
            reply_markup=ReplyKeyboardRemove(),
        )


@ROUTER.message(Command(commands={"analytics"}))
async def analytics_handler(message: Message) -> None:
    """Show system-wide analytics (admin command)."""
    
    track_command("analytics")
    
    LOGGER.info("Analytics command received from user_id=%s", message.from_user.id)
    
    try:
        from .analytics import AnalyticsCollector, get_metrics_counter
        
        # Get session factory from bot
        engine_attr = getattr(message.bot, "_dating_bot_context", {}).get("engine")
        if not engine_attr:
            await message.answer(
                "Аналитика недоступна. База данных не подключена.",
                reply_markup=ReplyKeyboardRemove(),
            )
            return
        
        from sqlalchemy.ext.asyncio import async_sessionmaker
        session_factory = async_sessionmaker(engine_attr, expire_on_commit=False)
        
        # Get analytics data
        collector = AnalyticsCollector(session_factory)
        metrics = await collector.get_overall_metrics()
        
        # Get real-time metrics
        rt_metrics = get_metrics_counter().get_metrics()
        
        # Build response
        response_lines = [
            "📊 <b>Системная аналитика</b>\n",
            "<b>👥 Пользователи:</b>",
            f"  • Всего: {metrics.total_users}",
            f"  • Средний возраст: {metrics.avg_age:.1f} лет",
            f"  • Вовлечённость: {metrics.engagement_rate:.1f}%",
        ]
        
        if metrics.gender_distribution:
            response_lines.append("\n<b>🚹🚺 Распределение по полу:</b>")
            for gender, count in metrics.gender_distribution.items():
                response_lines.append(f"  • {gender}: {count}")
        
        response_lines.extend([
            f"\n<b>💑 Взаимодействия:</b>",
            f"  • Матчей: {metrics.total_matches}",
            f"  • Лайков: {metrics.likes_sent}",
            f"  • Дизлайков: {metrics.dislikes_sent}",
            f"  • Match rate: {metrics.match_rate:.1f}%",
        ])
        
        if metrics.location_distribution:
            response_lines.append("\n<b>📍 Топ локаций:</b>")
            for location, count in list(metrics.location_distribution.items())[:5]:
                response_lines.append(f"  • {location}: {count}")
        
        if metrics.goal_distribution:
            response_lines.append("\n<b>🎯 Цели знакомства:</b>")
            for goal, count in metrics.goal_distribution.items():
                response_lines.append(f"  • {goal}: {count}")
        
        # Add real-time metrics
        if rt_metrics["counters"]:
            response_lines.append("\n<b>⚡ Метрики в реальном времени:</b>")
            uptime_hours = rt_metrics["uptime_seconds"] / 3600
            response_lines.append(f"  • Uptime: {uptime_hours:.1f}ч")
            
            commands_total = rt_metrics["counters"].get("commands_total", 0)
            interactions_total = rt_metrics["counters"].get("interactions_total", 0)
            
            if commands_total > 0:
                response_lines.append(f"  • Команд выполнено: {commands_total}")
            if interactions_total > 0:
                response_lines.append(f"  • Взаимодействий: {interactions_total}")
        
        response_message = "\n".join(response_lines)
        await message.answer(response_message, parse_mode=ParseMode.HTML)
        
    except Exception as exc:
        LOGGER.exception("Error getting analytics: %s", exc)
        await message.answer(
            "Произошла ошибка при получении аналитики. Попробуйте позже.",
            reply_markup=ReplyKeyboardRemove(),
        )


@ROUTER.message(F.web_app_data)
async def webapp_handler(message: Message) -> None:
    """Handle data submitted from the Telegram WebApp."""
    
    LOGGER.info("WebApp data received from user_id=%s", message.from_user.id)
    
    # Apply rate limiting
    try:
        rate_limiter = get_rate_limiter(message.bot)
        if not rate_limiter.is_allowed(message.from_user.id):
            remaining = rate_limiter.get_remaining_requests(message.from_user.id)
            LOGGER.warning(
                "Rate limit exceeded for user_id=%s (remaining: %d)",
                message.from_user.id, remaining
            )
            await message.answer(
                "Слишком много запросов. Пожалуйста, подождите немного перед следующей попыткой."
            )
            return
    except RuntimeError as exc:
        LOGGER.warning("Rate limiter unavailable: %s", exc)
        # Continue without rate limiting if it's not available

    web_app_data = message.web_app_data
    if not web_app_data:
        LOGGER.error("WebApp data is None for user_id=%s", message.from_user.id)
        await message.answer("Не удалось получить данные из мини-приложения.")
        return

    try:
        payload = json.loads(web_app_data.data)
        LOGGER.info("Parsed payload from user_id=%s, action=%s", message.from_user.id, payload.get("action", "create_profile"))
        
        # Check action type
        action = payload.get("action")
        
        # Handle delete action
        if action == "delete":
            LOGGER.info("Delete action requested by user_id=%s", message.from_user.id)
            try:
                repository = get_repository(message.bot)
            except RuntimeError as exc:
                LOGGER.exception("Profile repository is unavailable: %s", exc)
                await message.answer(
                    "Не удалось удалить профиль из-за внутренней ошибки. Попробуйте позже.",
                )
                return
            
            deleted = await repository.delete(message.from_user.id)
            if deleted:
                LOGGER.info("Profile deleted successfully for user_id=%s", message.from_user.id)
                await message.answer(
                    "Твой профиль удалён. Напиши /start, если захочешь создать новую анкету."
                )
            else:
                LOGGER.warning("Profile not found for deletion, user_id=%s", message.from_user.id)
                await message.answer(
                    "Профиль не найден."
                )
            return
        
        # Handle interaction actions (like/dislike)
        if action in ["like", "dislike"]:
            target_user_id = payload.get("target_user_id")
            if not target_user_id:
                await message.answer("Некорректный запрос: не указан пользователь.")
                return
            
            try:
                target_user_id = int(target_user_id)
            except (ValueError, TypeError):
                await message.answer("Некорректный ID пользователя.")
                return
            
            await handle_interaction(message, message.from_user.id, target_user_id, action)
            return
        
        # Handle settings update
        if action == "update_settings":
            LOGGER.info("Settings update requested by user_id=%s", message.from_user.id)
            try:
                settings_repo = get_settings_repository(message.bot)
            except RuntimeError as exc:
                LOGGER.exception("Settings repository is unavailable: %s", exc)
                await message.answer(
                    "Не удалось сохранить настройки из-за внутренней ошибки. Попробуйте позже.",
                )
                return
            
            # Extract settings from payload
            settings_data = {}
            for key in ["lang", "show_location", "show_age", "notify_matches", "notify_messages", 
                       "age_min", "age_max", "max_distance"]:
                if key in payload:
                    settings_data[key] = payload[key]
            
            try:
                await settings_repo.upsert(message.from_user.id, **settings_data)
                LOGGER.info("Settings updated for user_id=%s", message.from_user.id)
                await message.answer("✅ Настройки сохранены!")
            except OperationalError as exc:
                LOGGER.error("Database connection error when saving settings: %s", exc)
                await message.answer("Не удалось подключиться к базе данных. Попробуйте позже.")
            except SQLAlchemyError as exc:
                LOGGER.exception("Database error when saving settings: %s", exc)
                await message.answer("Не удалось сохранить настройки. Попробуйте позже.")
            except Exception as exc:
                LOGGER.exception("Unexpected error when saving settings: %s", exc)
                await message.answer("Не удалось сохранить настройки. Попробуйте позже.")
            return
        
        # Handle get recommendations request
        if action == "get_recommendations":
            LOGGER.info("Get recommendations requested by user_id=%s", message.from_user.id)
            try:
                profile_repo = get_repository(message.bot)
                interaction_repo = get_interaction_repository(message.bot)
                settings_repo = get_settings_repository(message.bot)
            except RuntimeError as exc:
                LOGGER.exception("Repositories are unavailable: %s", exc)
                await message.answer(
                    "Не удалось получить рекомендации. Попробуйте позже.",
                )
                return
            
            # Get user's profile
            user_profile = await profile_repo.get(message.from_user.id)
            if not user_profile:
                LOGGER.warning("Profile not found for user_id=%s", message.from_user.id)
                await message.answer(
                    "Сначала создайте профиль, чтобы получить рекомендации."
                )
                return
            
            # Get user preferences
            user_settings = await settings_repo.get(message.from_user.id)
            
            # Get already interacted users to exclude them
            liked_users = await interaction_repo.get_liked_users(message.from_user.id)
            disliked_users = await interaction_repo.get_disliked_users(message.from_user.id)
            interacted_users = set(liked_users + disliked_users)
            
            # Get best matches
            profile_obj = user_profile.to_profile()
            all_matches = await profile_repo.find_best_matches(profile_obj, limit=50)
            
            # Filter by user preferences
            filtered_matches = []
            for match_profile in all_matches:
                # Skip already interacted users
                if match_profile.user_id in interacted_users:
                    continue
                
                # Apply age filter if set
                if user_settings and user_settings.age_min is not None:
                    if match_profile.age < user_settings.age_min:
                        continue
                if user_settings and user_settings.age_max is not None:
                    if match_profile.age > user_settings.age_max:
                        continue
                
                filtered_matches.append(match_profile)
                
                # Limit to 10 recommendations per request
                if len(filtered_matches) >= 10:
                    break
            
            # Format response
            recommendations = []
            for match in filtered_matches:
                rec = {
                    "id": match.user_id,
                    "name": match.name,
                    "age": match.age,
                    "gender": match.gender,
                    "bio": match.bio,
                    "location": match.location,
                    "interests": match.interests,
                    "goal": match.goal,
                    "photo_url": match.photo_url
                }
                recommendations.append(rec)
            
            # Send recommendations back to webapp
            response_data = {
                "action": "recommendations",
                "profiles": recommendations,
                "count": len(recommendations)
            }
            
            await message.answer(
                json.dumps(response_data, ensure_ascii=False),
                parse_mode=None
            )
            LOGGER.info("Sent %d recommendations to user_id=%s", len(recommendations), message.from_user.id)
            return
        
        # Handle profile creation/update (default action)
        LOGGER.info("Processing profile data from user_id=%s", message.from_user.id)
        
        # Validate profile data using security module
        is_valid, error_msg = validate_profile_data(payload)
        if not is_valid:
            LOGGER.warning("Profile validation failed for user_id=%s: %s", message.from_user.id, error_msg)
            await message.answer(f"Некорректные данные профиля: {error_msg}")
            return
        
        # Sanitize text fields
        if 'name' in payload:
            payload['name'] = sanitize_user_input(str(payload['name']), max_length=100)
        if 'bio' in payload:
            payload['bio'] = sanitize_user_input(str(payload['bio']), max_length=1000)
        if 'location' in payload:
            payload['location'] = sanitize_user_input(str(payload['location']), max_length=200)
        if 'interests' in payload and isinstance(payload['interests'], list):
            payload['interests'] = [
                sanitize_user_input(str(interest), max_length=50)
                for interest in payload['interests']
            ]
        
        profile = build_profile_from_payload(message.from_user.id, payload)
        LOGGER.debug("Profile built successfully: %s", profile)
    except (json.JSONDecodeError, ValueError) as exc:
        LOGGER.error("Failed to process webapp data from user_id=%s: %s", message.from_user.id, exc)
        await message.answer(f"Не удалось обработать данные мини-приложения: {exc}")
        return

    await finalize_profile(message, profile)


def _format_match_message(profile: Profile) -> str:
    preference = {
        "male": "мужчин",
        "female": "женщин",
        "other": "людей вне бинарной системы",
        "any": "людей разного пола",
    }[profile.preference]
    lines = [
        "Нашлась подходящая анкета!",
        f"{profile.name}, {profile.age} лет.",
        f"Ищет: {preference}.",
    ]
    if profile.location:
        lines.append(f"Находится: {profile.location}.")
    if profile.goal:
        goal_title = GOAL_TITLES.get(profile.goal, profile.goal)
        lines.append(f"Цель знакомства: {goal_title}.")
    if profile.interests:
        interests = ", ".join(profile.interests)
        lines.append(f"Интересы: {interests}.")
    if profile.bio:
        lines.append(f"О себе: {profile.bio}")
    return "\n".join(lines)


async def _send_photo_reply(message: Message, profile: Profile) -> None:
    if profile.photo_file_id:
        await message.answer_photo(profile.photo_file_id)
    elif profile.photo_url:
        await message.answer(f"Фото: {profile.photo_url}")


async def _send_profile_photo(bot: Bot, chat_id: int, profile: Profile) -> None:
    if profile.photo_file_id:
        await bot.send_photo(chat_id=chat_id, photo=profile.photo_file_id)
    elif profile.photo_url:
        await bot.send_message(chat_id=chat_id, text=f"Фото: {profile.photo_url}")


async def main() -> None:
    """Bootstrap the bot."""
    
    # Enable debug logging - can be controlled via DEBUG environment variable
    log_level = logging.DEBUG if os.getenv("DEBUG", "").lower() in ("true", "1", "yes") else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    LOGGER.info("Starting bot with log level: %s", logging.getLevelName(log_level))

    config = load_config()
    LOGGER.debug("Configuration loaded: webapp_url=%s", config.webapp_url)
    
    engine = create_async_engine(config.database_url, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    # Test database connection before starting the bot
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        LOGGER.info("Database connection successful")
    except Exception as exc:
        LOGGER.error("Failed to connect to database: %s", exc)
        await engine.dispose()
        raise RuntimeError(
            "Cannot connect to database. Please check your BOT_DATABASE_URL "
            "and ensure the database server is running."
        ) from exc

    bot = Bot(
        token=config.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    profile_repository = ProfileRepository(session_factory)
    settings_repository = UserSettingsRepository(session_factory)
    interaction_repository = InteractionRepository(session_factory)
    match_repository = MatchRepository(session_factory)
    
    # Initialize rate limiter with custom configuration
    rate_limit_config = RateLimitConfig(
        max_requests=20,  # 20 requests per user
        window_seconds=60  # per minute
    )
    rate_limiter = RateLimiter(rate_limit_config)
    LOGGER.info("Rate limiter initialized: %d requests per %d seconds", 
               rate_limit_config.max_requests, rate_limit_config.window_seconds)
    
    attach_bot_context(
        bot, config, profile_repository, settings_repository, 
        interaction_repository, match_repository, rate_limiter, engine
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(ROUTER)

    LOGGER.info("Starting polling")
    try:
        await dp.start_polling(bot)
    finally:
        LOGGER.info("Shutting down bot")
        await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped")
