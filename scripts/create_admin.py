#!/usr/bin/env python3
"""Script to create a new admin user."""

import asyncio
import hashlib
import os
import sys
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.db import Admin


def hash_password(password: str) -> str:
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


async def create_admin(
    username: str,
    password: str,
    full_name: str = None,
    email: str = None,
    is_super_admin: bool = False,
):
    """Create a new admin user."""
    # Get database URL from environment
    database_url = os.getenv(
        "DATABASE_URL", "postgresql+asyncpg://dating:dating@localhost:5432/dating"
    )

    # Create engine and session
    engine = create_async_engine(database_url, echo=False)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with session_maker() as session:
        # Check if username already exists
        result = await session.execute(select(Admin).where(Admin.username == username))
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            print(f"❌ Администратор с username '{username}' уже существует!")
            return False

        # Create new admin
        admin = Admin(
            username=username,
            password_hash=hash_password(password),
            full_name=full_name,
            email=email,
            is_active=True,
            is_super_admin=is_super_admin,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        session.add(admin)
        await session.commit()

        print(f"✅ Администратор '{username}' успешно создан!")
        print(f"   Полное имя: {full_name or 'не указано'}")
        print(f"   Email: {email or 'не указан'}")
        print(f"   Супер-админ: {'Да' if is_super_admin else 'Нет'}")
        return True


async def list_admins():
    """List all admin users."""
    database_url = os.getenv(
        "DATABASE_URL", "postgresql+asyncpg://dating:dating@localhost:5432/dating"
    )

    engine = create_async_engine(database_url, echo=False)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with session_maker() as session:
        result = await session.execute(select(Admin).order_by(Admin.id))
        admins = result.scalars().all()

        if not admins:
            print("❌ Администраторы не найдены в базе данных")
            return

        print(f"\n{'='*80}")
        print(
            f"{'ID':<5} {'Username':<20} {'Full Name':<25} {'Super Admin':<12} {'Active'}"
        )
        print(f"{'='*80}")

        for admin in admins:
            print(
                f"{admin.id:<5} "
                f"{admin.username:<20} "
                f"{(admin.full_name or '-'):<25} "
                f"{'Yes' if admin.is_super_admin else 'No':<12} "
                f"{'Yes' if admin.is_active else 'No'}"
            )

        print(f"{'='*80}\n")


async def change_password(username: str, new_password: str):
    """Change admin password."""
    database_url = os.getenv(
        "DATABASE_URL", "postgresql+asyncpg://dating:dating@localhost:5432/dating"
    )

    engine = create_async_engine(database_url, echo=False)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with session_maker() as session:
        result = await session.execute(select(Admin).where(Admin.username == username))
        admin = result.scalar_one_or_none()

        if not admin:
            print(f"❌ Администратор '{username}' не найден!")
            return False

        admin.password_hash = hash_password(new_password)
        admin.updated_at = datetime.now(UTC)
        await session.commit()

        print(f"✅ Пароль для '{username}' успешно изменен!")
        return True


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Использование:")
        print(
            "  python scripts/create_admin.py create <username> <password> [full_name] [email] [--super-admin]"
        )
        print("  python scripts/create_admin.py list")
        print(
            "  python scripts/create_admin.py change-password <username> <new_password>"
        )
        print("\nПримеры:")
        print("  python scripts/create_admin.py create admin admin123")
        print(
            "  python scripts/create_admin.py create john secretpass 'John Doe' john@example.com --super-admin"
        )
        print("  python scripts/create_admin.py list")
        print("  python scripts/create_admin.py change-password admin newpass123")
        return

    command = sys.argv[1]

    if command == "create":
        if len(sys.argv) < 4:
            print("❌ Недостаточно аргументов для создания администратора")
            print(
                "Использование: create <username> <password> [full_name] [email] [--super-admin]"
            )
            return

        username = sys.argv[2]
        password = sys.argv[3]
        full_name = (
            sys.argv[4]
            if len(sys.argv) > 4 and not sys.argv[4].startswith("--")
            else None
        )
        email = (
            sys.argv[5]
            if len(sys.argv) > 5 and not sys.argv[5].startswith("--")
            else None
        )
        is_super_admin = "--super-admin" in sys.argv

        asyncio.run(create_admin(username, password, full_name, email, is_super_admin))

    elif command == "list":
        asyncio.run(list_admins())

    elif command == "change-password":
        if len(sys.argv) < 4:
            print("❌ Недостаточно аргументов для смены пароля")
            print("Использование: change-password <username> <new_password>")
            return

        username = sys.argv[2]
        new_password = sys.argv[3]
        asyncio.run(change_password(username, new_password))

    else:
        print(f"❌ Неизвестная команда: {command}")
        print("Доступные команды: create, list, change-password")


if __name__ == "__main__":
    main()
