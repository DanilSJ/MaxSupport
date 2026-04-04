from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.models import User, Chat
from typing import List, Optional


async def get_all_users(session: AsyncSession) -> List[User]:
    """Получить всех пользователей"""
    stmt = select(User)
    result = await session.execute(stmt)
    users = result.scalars().all()
    return list(users)


async def get_user(session: AsyncSession, max_id: int) -> User | None:
    """Получить пользователя по max_id"""
    stmt = select(User).where(User.max_id == max_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_all_chats(session: AsyncSession) -> List[Chat]:
    """Получить все города (чаты)"""
    stmt = select(Chat)
    result = await session.execute(stmt)
    chats = result.scalars().all()
    return list(chats)


async def get_users_by_chat(session: AsyncSession, chat_id: int) -> List[User]:
    """Получить всех пользователей определенного города"""
    stmt = select(User).where(User.chat_id == chat_id)
    result = await session.execute(stmt)
    users = result.scalars().all()
    return list(users)


async def get_chat_by_name(session: AsyncSession, name: str) -> Optional[Chat]:
    """Получить город по названию"""
    stmt = select(Chat).where(Chat.name == name)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()