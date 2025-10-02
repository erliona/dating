"""Example profile handler for Epic B - Onboarding integration.

This example shows how to integrate profile creation, validation, and photo upload
into a Telegram bot using the Epic B functionality.
"""

import json
import logging
from datetime import datetime
from typing import Any

from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from bot.config import load_config
from bot.geo import process_location_data
from bot.media import PhotoValidationError, validate_and_process_photo
from bot.repository import ProfileRepository
from bot.security import validate_webapp_init_data
from bot.validation import validate_profile_data

logger = logging.getLogger(__name__)

# Example router for profile operations
profile_router = Router()


async def handle_webapp_data(message: types.Message, bot: Bot):
    """Handle data received from WebApp.
    
    This handler processes profile data submitted from the Mini App,
    including validation, photo processing, and database storage.
    """
    if not message.web_app_data:
        await message.answer("No WebApp data received")
        return
    
    try:
        # Parse WebApp data
        data = json.loads(message.web_app_data.data)
        action = data.get("action")
        
        logger.info(
            f"WebApp data received: {action}",
            extra={"event_type": "webapp_data_received", "user_id": message.from_user.id}
        )
        
        # Get database session from bot context
        session_maker = bot.get("session_maker")
        if not session_maker:
            await message.answer("❌ Database not configured")
            return
        
        async with session_maker() as session:
            repository = ProfileRepository(session)
            
            if action == "create_profile":
                await handle_create_profile(message, data, repository, session)
            elif action == "update_profile":
                await handle_update_profile(message, data, repository, session)
            elif action == "add_photo":
                await handle_add_photo(message, data, repository, session)
            else:
                await message.answer(f"❌ Unknown action: {action}")
    
    except json.JSONDecodeError:
        logger.error("Failed to parse WebApp data", exc_info=True)
        await message.answer("❌ Invalid data format")
    except Exception as exc:
        logger.error(f"Error processing WebApp data: {exc}", exc_info=True)
        await message.answer("❌ Failed to process data")


async def handle_create_profile(
    message: types.Message,
    data: dict,
    repository: ProfileRepository,
    session: AsyncSession
):
    """Handle profile creation."""
    profile_data = data.get("profile", {})
    
    # Validate profile data
    is_valid, error = validate_profile_data(profile_data)
    if not is_valid:
        await message.answer(f"❌ Validation error: {error}")
        return
    
    # Create or update user
    user = await repository.create_or_update_user(
        tg_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        language_code=message.from_user.language_code,
        is_premium=message.from_user.is_premium or False
    )
    
    # Process location data
    location = process_location_data(
        latitude=profile_data.get("latitude"),
        longitude=profile_data.get("longitude"),
        country=profile_data.get("country"),
        city=profile_data.get("city")
    )
    
    # Add location to profile data
    profile_data.update(location)
    
    # Convert birth_date string to date object if needed
    if "birth_date" in profile_data and isinstance(profile_data["birth_date"], str):
        profile_data["birth_date"] = datetime.strptime(
            profile_data["birth_date"], "%Y-%m-%d"
        ).date()
    
    # Mark profile as complete if all required data is present
    profile_data["is_complete"] = True
    
    # Create profile
    profile = await repository.create_profile(user.id, profile_data)
    await session.commit()
    
    logger.info(
        "Profile created successfully",
        extra={
            "event_type": "profile_created",
            "user_id": message.from_user.id,
            "profile_id": profile.id
        }
    )
    
    await message.answer(
        "✅ Профиль создан!\n\n"
        f"Имя: {profile.name}\n"
        f"Возраст: {profile.birth_date}\n"
        f"Пол: {profile.gender}\n"
        f"Цель: {profile.goal}\n"
        f"Город: {profile.city or 'не указан'}"
    )


async def handle_update_profile(
    message: types.Message,
    data: dict,
    repository: ProfileRepository,
    session: AsyncSession
):
    """Handle profile update."""
    profile_data = data.get("profile", {})
    
    # Get user
    user = await repository.get_user_by_tg_id(message.from_user.id)
    if not user:
        await message.answer("❌ User not found. Please create profile first.")
        return
    
    # Update profile
    profile = await repository.update_profile(user.id, profile_data)
    if not profile:
        await message.answer("❌ Profile not found. Please create profile first.")
        return
    
    await session.commit()
    
    logger.info(
        "Profile updated successfully",
        extra={
            "event_type": "profile_updated",
            "user_id": message.from_user.id,
            "profile_id": profile.id
        }
    )
    
    await message.answer("✅ Профиль обновлен!")


async def handle_add_photo(
    message: types.Message,
    data: dict,
    repository: ProfileRepository,
    session: AsyncSession
):
    """Handle photo upload."""
    photo_data = data.get("photo")
    if not photo_data:
        await message.answer("❌ No photo data provided")
        return
    
    # Get user
    user = await repository.get_user_by_tg_id(message.from_user.id)
    if not user:
        await message.answer("❌ User not found. Please create profile first.")
        return
    
    # Check photo count limit
    existing_photos = await repository.get_user_photos(user.id)
    if len(existing_photos) >= 3:
        await message.answer("❌ Maximum 3 photos allowed")
        return
    
    try:
        # Validate and process photo
        processed = validate_and_process_photo(photo_data, user.id)
        
        # Add photo to database
        photo = await repository.add_photo(
            user_id=user.id,
            url=processed["url"],
            sort_order=len(existing_photos),
            safe_score=processed["safe_score"],
            file_size=processed["file_size"],
            mime_type=processed["mime_type"]
        )
        
        await session.commit()
        
        logger.info(
            "Photo added successfully",
            extra={
                "event_type": "photo_added",
                "user_id": message.from_user.id,
                "photo_id": photo.id
            }
        )
        
        await message.answer(
            f"✅ Фото добавлено!\n"
            f"Размер: {processed['file_size'] // 1024}KB\n"
            f"Рейтинг безопасности: {processed['safe_score']:.2f}"
        )
    
    except PhotoValidationError as e:
        await message.answer(f"❌ Ошибка валидации фото: {e}")
    except Exception as e:
        logger.error(f"Failed to add photo: {e}", exc_info=True)
        await message.answer("❌ Не удалось добавить фото")


@profile_router.message(Command("profile"))
async def cmd_profile(message: types.Message):
    """Show profile command."""
    # Get database session from bot context
    session_maker = message.bot.get("session_maker")
    if not session_maker:
        await message.answer("❌ Database not configured")
        return
    
    async with session_maker() as session:
        repository = ProfileRepository(session)
        
        # Get user
        user = await repository.get_user_by_tg_id(message.from_user.id)
        if not user:
            await message.answer(
                "У вас еще нет профиля.\n"
                "Создайте профиль через Mini App!"
            )
            return
        
        # Get profile
        profile = await repository.get_profile_by_user_id(user.id)
        if not profile:
            await message.answer(
                "У вас еще нет профиля.\n"
                "Создайте профиль через Mini App!"
            )
            return
        
        # Get photos
        photos = await repository.get_user_photos(user.id)
        
        # Format profile info
        profile_text = (
            f"👤 Ваш профиль\n\n"
            f"Имя: {profile.name}\n"
            f"Возраст: {(datetime.now().date() - profile.birth_date).days // 365}\n"
            f"Пол: {profile.gender}\n"
            f"Ориентация: {profile.orientation}\n"
            f"Цель: {profile.goal}\n"
        )
        
        if profile.bio:
            profile_text += f"\nО себе: {profile.bio}\n"
        
        if profile.interests:
            profile_text += f"\nИнтересы: {', '.join(profile.interests)}\n"
        
        if profile.city:
            profile_text += f"\nГород: {profile.city}\n"
        
        profile_text += f"\nФотографий: {len(photos)}/3\n"
        profile_text += f"Профиль заполнен: {'✅' if profile.is_complete else '❌'}"
        
        await message.answer(profile_text)


async def setup_profile_handlers(dp: Dispatcher, bot: Bot, config):
    """Setup profile handlers with database connection."""
    # Create database engine
    engine = create_async_engine(config.database_url, echo=False)
    
    # Create session maker
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Store session maker in bot context
    bot["session_maker"] = async_session_maker
    
    # Register router
    dp.include_router(profile_router)
    
    # Register WebApp data handler
    dp.message.register(handle_webapp_data, lambda m: m.web_app_data is not None)
    
    logger.info("Profile handlers setup complete")


async def main():
    """Example main function."""
    config = load_config()
    
    bot = Bot(token=config.token)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Setup profile handlers
    await setup_profile_handlers(dp, bot, config)
    
    # Start polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
