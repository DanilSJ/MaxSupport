from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.models import User
from typing import List


async def get_all_users(session: AsyncSession) -> List[User]:
    stmt = select(User)
    result = await session.execute(stmt)
    users = result.scalars().all()
    return list(users)

async def get_user(session: AsyncSession, max_id: int) -> User | None:
    stmt = select(User).where(User.max_id == max_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()