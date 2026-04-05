from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.models import Chat, User


def normalize_words(name: str) -> set[str]:
    """
    Приводим к нижнему регистру, заменяем дефисы на пробелы,
    и разбиваем на отдельные слова, возвращаем как множество
    """
    name = name.lower().replace("-", " ")
    words = set(name.split())
    return words

async def get_chat_by_name(session: AsyncSession, name: str) -> Optional[Chat]:
    input_words = normalize_words(name.lower())

    stmt = select(Chat)
    result = await session.execute(stmt)
    chats = result.scalars().all()

    for chat in chats:
        chat_words = normalize_words(chat.name)
        if input_words <= chat_words:
            return chat

    return None

async def update_user_chat(session: AsyncSession, max_id: int, chat_id: int) -> User | None:
    stmt = select(User).where(User.max_id == max_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        return None

    user.chat_id = chat_id

    await session.commit()
    return user