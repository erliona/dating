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
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup, Message,
                           ReplyKeyboardRemove, WebAppData, WebAppInfo)

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from .config import BotConfig, load_config
from .db import (
    InteractionRepository,
    MatchRepository,
    ProfileRepository,
    UserSettingsRepository,
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
) -> None:
    """Populate the bot context with common application dependencies."""

    _set_bot_context_value(bot, CONFIG_CONTEXT_KEY, config)
    _set_bot_context_value(bot, REPOSITORY_CONTEXT_KEY, repository)
    _set_bot_context_value(bot, SETTINGS_REPOSITORY_KEY, settings_repository)
    _set_bot_context_value(bot, INTERACTION_REPOSITORY_KEY, interaction_repository)
    _set_bot_context_value(bot, MATCH_REPOSITORY_KEY, match_repository)


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
    """Handle like/dislike interaction between users."""
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
    except Exception as exc:
        LOGGER.exception("Failed to save interaction: %s", exc)
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
            except Exception as exc:
                LOGGER.exception("Failed to create match: %s", exc)
                await message.answer("🎉 У вас взаимная симпатия!")
        else:
            # Like sent but no match yet
            await message.answer("✅ Симпатия отправлена!")
    else:
        # Dislike - just confirm
        await message.answer("👌 Понятно, продолжаем поиск!")


async def finalize_profile(message: Message, profile: Profile, is_update: bool = False) -> None:
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
    except Exception as exc:  # pragma: no cover - debug assistance
        LOGGER.exception(
            "Error while saving profile for user_id=%s: %s", profile.user_id, exc
        )
        await message.answer(
            f"Не удалось сохранить анкету. Ошибка: {exc}",
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

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть мини-приложение",
                    web_app=WebAppInfo(url=config.webapp_url),
                )
            ]
        ]
    )

    LOGGER.debug("Sending webapp button to user_id=%s with url=%s", 
                 message.from_user.id, config.webapp_url)
    await message.answer("\n".join(greeting), reply_markup=keyboard)


@ROUTER.message(Command(commands={"cancel", "reset"}))
async def cancel_handler(message: Message, state: FSMContext) -> None:
    """Allow users to cancel any ongoing state."""

    await state.clear()
    await message.answer(
        "Все операции отменены. Напиши /start, чтобы начать.",
        reply_markup=ReplyKeyboardRemove(),
    )


@ROUTER.message(Command(commands={"debug"}))
async def debug_handler(message: Message) -> None:
    """Show comprehensive debug information about the bot's status."""
    
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


@ROUTER.message(F.web_app_data)
async def webapp_handler(message: Message) -> None:
    """Handle data submitted from the Telegram WebApp."""
    
    LOGGER.debug("WebApp data received from user_id=%s", message.from_user.id)

    web_app_data = message.web_app_data
    if not web_app_data:
        LOGGER.error("WebApp data is None for user_id=%s", message.from_user.id)
        await message.answer("Не удалось получить данные из мини-приложения.")
        return

    try:
        payload = json.loads(web_app_data.data)
        LOGGER.debug("Parsed payload: %s", payload)
        
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
            for key in ["lang", "show_location", "show_age", "notify_matches", "notify_messages"]:
                if key in payload:
                    settings_data[key] = payload[key]
            
            try:
                await settings_repo.upsert(message.from_user.id, **settings_data)
                LOGGER.info("Settings updated for user_id=%s", message.from_user.id)
                await message.answer("✅ Настройки сохранены!")
            except Exception as exc:
                LOGGER.exception("Failed to save settings: %s", exc)
                await message.answer("Не удалось сохранить настройки.")
            return
        
        # Handle profile creation/update (default action)
        LOGGER.info("Processing profile data from user_id=%s", message.from_user.id)
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
    attach_bot_context(
        bot, config, profile_repository, settings_repository, interaction_repository, match_repository
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
