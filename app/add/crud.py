from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.models import Chat, User


async def get_chat_by_name(session: AsyncSession, name: str) -> Chat | None:
    stmt = select(Chat).where(Chat.name.ilike(name))
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def update_user_chat(session: AsyncSession, max_id: int, chat_id: int) -> User | None:
    stmt = select(User).where(User.max_id == max_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        return None

    user.chat_id = chat_id

    await session.commit()
    return user