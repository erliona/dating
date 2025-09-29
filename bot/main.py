"""Entry point for the dating Telegram bot."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup, Message,
                           ReplyKeyboardRemove, WebAppData, WebAppInfo)

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from .config import BotConfig, load_config
from .db import ProfileRepository


LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class Profile:
    """User profile collected from the in-bot questionnaire."""

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


class Questionnaire(StatesGroup):
    """Conversation states for the onboarding questionnaire."""

    waiting_for_name = State()
    waiting_for_age = State()
    waiting_for_gender = State()
    waiting_for_preference = State()
    waiting_for_bio = State()
    waiting_for_location = State()
    waiting_for_interests = State()
    waiting_for_goal = State()
    waiting_for_photo = State()


PROFILE_REPOSITORY: ProfileRepository | None = None
CONFIG: BotConfig | None = None
ROUTER = Router()


def get_config() -> BotConfig:
    if CONFIG is None:
        raise RuntimeError("Bot configuration is not loaded")
    return CONFIG


def get_repository() -> ProfileRepository:
    if PROFILE_REPOSITORY is None:
        raise RuntimeError("Profile repository is not initialized")
    return PROFILE_REPOSITORY


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


async def finalize_profile(message: Message, profile: Profile) -> None:
    repository = get_repository()
    await repository.upsert(profile)
    match = await repository.find_mutual_match(profile)

    if match:
        await message.answer(
            _format_match_message(match),
            reply_markup=ReplyKeyboardRemove(),
        )
        await _send_photo_reply(message, match)
        await message.bot.send_message(
            chat_id=match.user_id,
            text=_format_match_message(profile),
            reply_markup=ReplyKeyboardRemove(),
        )
        await _send_profile_photo(message.bot, match.user_id, profile)
    else:
        await message.answer(
            "Спасибо! Как только мы найдём подходящую пару, я сразу дам знать.",
            reply_markup=ReplyKeyboardRemove(),
        )


@ROUTER.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    """Handle the /start command."""

    config = get_config()
    await state.clear()
    greeting = [
        "Привет! Я бот для знакомств.",
        "Ответь на несколько вопросов, чтобы мы могли подобрать тебе пару.",
        "Как тебя зовут?",
    ]

    keyboard = ReplyKeyboardRemove()
    if config.webapp_url:
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

    await message.answer("\n".join(greeting), reply_markup=keyboard)
    await state.set_state(Questionnaire.waiting_for_name)


@ROUTER.message(Command(commands={"cancel", "reset"}))
async def cancel_handler(message: Message, state: FSMContext) -> None:
    """Allow users to cancel the questionnaire."""

    await state.clear()
    await message.answer(
        "Анкета сброшена. Напиши /start, чтобы пройти её заново.",
        reply_markup=ReplyKeyboardRemove(),
    )


@ROUTER.message(Questionnaire.waiting_for_name)
async def name_handler(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer("Пожалуйста, отправь имя текстом.")
        return

    await state.update_data(name=text)
    await message.answer("Сколько тебе лет?")
    await state.set_state(Questionnaire.waiting_for_age)


@ROUTER.message(Questionnaire.waiting_for_age)
async def age_handler(message: Message, state: FSMContext) -> None:
    try:
        age = int((message.text or "").strip())
        if age < 18:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введи реальный возраст (не моложе 18 лет).")
        return

    await state.update_data(age=age)
    await message.answer("Как ты себя идентифицируешь? (м/ж/другой)")
    await state.set_state(Questionnaire.waiting_for_gender)


@ROUTER.message(Questionnaire.waiting_for_gender)
async def gender_handler(message: Message, state: FSMContext) -> None:
    try:
        gender = normalise_choice(message.text or "")
        if gender == "any":
            raise ValueError
    except ValueError:
        await message.answer("Напиши 'м', 'ж' или 'другой'.")
        return

    await state.update_data(gender=gender)
    await message.answer("Кто тебе интересен? (м/ж/любой)")
    await state.set_state(Questionnaire.waiting_for_preference)


@ROUTER.message(Questionnaire.waiting_for_preference)
async def preference_handler(message: Message, state: FSMContext) -> None:
    try:
        preference = normalise_choice(message.text or "")
    except ValueError:
        await message.answer("Напиши 'м', 'ж' или 'любой'.")
        return

    await state.update_data(preference=preference)
    await message.answer(
        "Расскажи коротко о себе (или напиши '-' если хочешь пропустить)."
    )
    await state.set_state(Questionnaire.waiting_for_bio)


@ROUTER.message(Questionnaire.waiting_for_bio)
async def bio_handler(message: Message, state: FSMContext) -> None:
    bio_text = (message.text or "").strip()
    bio = None if bio_text == "-" else bio_text

    await state.update_data(bio=bio)
    await message.answer(
        "Где ты находишься? Укажи город или пришли геолокацию (можно '-' чтобы пропустить)."
    )
    await state.set_state(Questionnaire.waiting_for_location)


@ROUTER.message(Questionnaire.waiting_for_location)
async def location_handler(message: Message, state: FSMContext) -> None:
    if message.location:
        location_value = f"{message.location.latitude:.4f}, {message.location.longitude:.4f}"
    else:
        location_text = (message.text or "").strip()
        if not location_text or location_text == "-":
            location_value = None
        else:
            location_value = location_text

    await state.update_data(location=location_value)
    await message.answer(
        "Расскажи о своих интересах (через запятую) или '-' если хочешь пропустить."
    )
    await state.set_state(Questionnaire.waiting_for_interests)


@ROUTER.message(Questionnaire.waiting_for_interests)
async def interests_handler(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text or text == "-":
        interests: list[str] = []
    else:
        interests = [part.strip() for part in text.split(",") if part.strip()]

    await state.update_data(interests=interests)
    await message.answer(
        "Какова твоя цель знакомства? Напиши: серьёзные отношения, дружба, общение или лёгкие встречи (или '-' чтобы пропустить)."
    )
    await state.set_state(Questionnaire.waiting_for_goal)


@ROUTER.message(Questionnaire.waiting_for_goal)
async def goal_handler(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text or text == "-":
        goal_value: str | None = None
    else:
        try:
            goal_value = normalise_goal(text)
        except ValueError:
            await message.answer(
                "Укажи одну из целей: серьёзные отношения, дружба, общение или лёгкие встречи (можно '-' чтобы пропустить)."
            )
            return

    await state.update_data(goal=goal_value)
    await message.answer(
        "Пришли своё фото (можно ссылку) или '-' если хочешь пропустить."
    )
    await state.set_state(Questionnaire.waiting_for_photo)


@ROUTER.message(Questionnaire.waiting_for_photo)
async def photo_handler(message: Message, state: FSMContext) -> None:
    photo_file_id: str | None = None
    photo_url: str | None = None

    if message.photo:
        photo_file_id = message.photo[-1].file_id
    else:
        text = (message.text or "").strip()
        if not text or text == "-":
            photo_file_id = None
        elif text.lower().startswith(("http://", "https://")):
            photo_url = text
        else:
            await message.answer(
                "Пришли фотографию, ссылку на неё или '-' если хочешь пропустить."
            )
            return

    data = await state.get_data()
    profile = Profile(
        user_id=message.from_user.id,
        name=data["name"],
        age=data["age"],
        gender=data["gender"],
        preference=data["preference"],
        bio=data.get("bio"),
        location=data.get("location"),
        interests=data.get("interests", []),
        goal=data.get("goal"),
        photo_file_id=photo_file_id,
        photo_url=photo_url,
    )
    await state.clear()
    await finalize_profile(message, profile)


@ROUTER.message(F.web_app_data)
async def webapp_handler(message: Message, web_app_data: WebAppData) -> None:
    """Handle data submitted from the Telegram WebApp."""

    try:
        payload = json.loads(web_app_data.data)
        profile = build_profile_from_payload(message.from_user.id, payload)
    except (json.JSONDecodeError, ValueError) as exc:
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

    logging.basicConfig(level=logging.INFO)

    config = load_config()
    engine = create_async_engine(config.database_url, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    global PROFILE_REPOSITORY, CONFIG
    PROFILE_REPOSITORY = ProfileRepository(session_factory)
    CONFIG = config

    bot = Bot(
        token=config.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(ROUTER)

    logging.info("Starting polling")
    try:
        await dp.start_polling(bot)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped")
