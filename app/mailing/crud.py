from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.models import User
from typing import List


async def get_all_users(session: AsyncSession) -> List[User]:
    stmt = select(User)
    result = await session.execute(stmt)
    users = result.scalars().all()
    return list(users)
