"""Entry point for the dating Telegram bot."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Optional

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup, Message,
                           ReplyKeyboardRemove, WebAppData, WebAppInfo)

from .config import BotConfig, load_config


@dataclass(slots=True)
class Profile:
    """User profile collected from the in-bot questionnaire."""

    user_id: int
    name: str
    age: int
    gender: str
    preference: str
    bio: str | None = None


class Questionnaire(StatesGroup):
    """Conversation states for the onboarding questionnaire."""

    waiting_for_name = State()
    waiting_for_age = State()
    waiting_for_gender = State()
    waiting_for_preference = State()
    waiting_for_bio = State()


class ProfileStore:
    """A very small persistence layer for user profiles."""

    def __init__(self, path: Path | None):
        self._path = path
        self._profiles: Dict[int, Profile] = {}
        if path:
            self._path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> None:
        if not self._path or not self._path.exists():
            return
        data = json.loads(self._path.read_text(encoding="utf-8"))
        self._profiles = {
            int(user_id): Profile(**profile) for user_id, profile in data.items()
        }

    def save(self) -> None:
        if not self._path:
            return
        payload = {user_id: asdict(profile) for user_id, profile in self._profiles.items()}
        self._path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def upsert(self, profile: Profile) -> None:
        self._profiles[profile.user_id] = profile
        self.save()

    def get(self, user_id: int) -> Optional[Profile]:
        return self._profiles.get(user_id)

    def find_mutual_match(self, profile: Profile) -> Optional[Profile]:
        for other in self._profiles.values():
            if other.user_id == profile.user_id:
                continue
            if self._is_compatible(profile, other) and self._is_compatible(other, profile):
                return other
        return None

    @staticmethod
    def _is_compatible(profile: Profile, other: Profile) -> bool:
        return other.gender == profile.preference or profile.preference == "any"


PROFILE_STORE: ProfileStore
CONFIG: BotConfig
ROUTER = Router()


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

    return Profile(
        user_id=user_id,
        name=name,
        age=age,
        gender=gender,
        preference=preference,
        bio=bio_text,
    )


async def finalize_profile(message: Message, profile: Profile) -> None:
    PROFILE_STORE.upsert(profile)
    match = PROFILE_STORE.find_mutual_match(profile)

    if match:
        await message.answer(
            _format_match_message(match),
            reply_markup=ReplyKeyboardRemove(),
        )
        await message.bot.send_message(
            chat_id=match.user_id,
            text=_format_match_message(profile),
        )
    else:
        await message.answer(
            "Спасибо! Как только мы найдём подходящую пару, я сразу дам знать.",
            reply_markup=ReplyKeyboardRemove(),
        )


@ROUTER.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    """Handle the /start command."""

    await state.clear()
    greeting = [
        "Привет! Я бот для знакомств.",
        "Ответь на несколько вопросов, чтобы мы могли подобрать тебе пару.",
        "Как тебя зовут?",
    ]

    keyboard = ReplyKeyboardRemove()
    if CONFIG.webapp_url:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Открыть мини-приложение",
                        web_app=WebAppInfo(url=CONFIG.webapp_url),
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
    await state.update_data(name=message.text.strip())
    await message.answer("Сколько тебе лет?")
    await state.set_state(Questionnaire.waiting_for_age)


@ROUTER.message(Questionnaire.waiting_for_age)
async def age_handler(message: Message, state: FSMContext) -> None:
    try:
        age = int(message.text.strip())
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
        gender = normalise_choice(message.text)
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
        preference = normalise_choice(message.text)
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
    data = await state.get_data()
    bio_text = message.text.strip()
    bio = None if bio_text == "-" else bio_text

    profile = Profile(
        user_id=message.from_user.id,
        name=data["name"],
        age=data["age"],
        gender=data["gender"],
        preference=data["preference"],
        bio=bio,
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
    bio = f"\nО себе: {profile.bio}" if profile.bio else ""
    return (
        "Нашлась подходящая анкета!\n"
        f"{profile.name}, {profile.age} лет.\n"
        f"Ищет: {preference}.{bio}"
    )


async def main() -> None:
    """Bootstrap the bot."""

    logging.basicConfig(level=logging.INFO)

    config = load_config()
    storage_path = Path(config.storage_path) if config.storage_path else None
    global PROFILE_STORE, CONFIG
    PROFILE_STORE = ProfileStore(storage_path)
    PROFILE_STORE.load()
    CONFIG = config

    bot = Bot(token=config.token, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(ROUTER)

    logging.info("Starting polling")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped")
