from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from core.models import User


async def get_users_count(session: AsyncSession) -> int:
    stmt = select(func.count()).select_from(User)
    result = await session.execute(stmt)
    count = result.scalar_one()
    return count


async def get_user(session: AsyncSession, max_id: int) -> User | None:
    stmt = select(User).where(User.max_id == max_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()