from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.models import User, Chat
from typing import List


async def get_all_chats_id(session: AsyncSession) -> List[int]:
    stmt = select(Chat.chat_id)
    result = await session.execute(stmt)
    chat_ids = result.scalars().all()
    return list(chat_ids)


async def get_user_with_chat(session: AsyncSession, max_id: int) -> User:
    stmt = select(User).where(User.max_id == max_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    return user
