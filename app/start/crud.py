from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.models import User, Chat
from typing import List, Optional


async def create_user(session: AsyncSession, max_id: int, chat_id: int | None = None) -> User:
    stmt = select(User).where(User.max_id == max_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        user = User(max_id=max_id, chat_id=chat_id)
        session.add(user)
    else:
        if chat_id is not None:
            user.chat_id = chat_id  # обновляем

    await session.commit()
    return user


async def get_all_users(session: AsyncSession) -> List[User]:
    stmt = select(User)
    result = await session.execute(stmt)
    users = result.scalars().all()
    return list(users)


async def get_all_chat(session: AsyncSession) -> List[Chat]:
    stmt = select(Chat)
    result = await session.execute(stmt)
    chats = result.scalars().all()
    return list(chats)

async def get_chat_by_id(session: AsyncSession, chat_id: int, name_part: str | None = None) -> Optional[Chat]:
    stmt = select(Chat).where(Chat.chat_id == chat_id)
    result = await session.execute(stmt)
    chats = result.scalars().all()

    if not chats:
        return None

    if len(chats) == 1 or not name_part:
        return chats[0]

    for chat in chats:
        if name_part.lower() in chat.name.lower():
            return chat

    return chats[0]

async def get_child_chats(session: AsyncSession, parent_id: int):
    stmt = select(Chat).where(Chat.parent_id == parent_id)
    result = await session.execute(stmt)
    return result.scalars().all()

async def get_root_chats(session: AsyncSession) -> List[Chat]:
    stmt = select(Chat).where(Chat.parent_id == None)
    result = await session.execute(stmt)
    return list(result.scalars().all())