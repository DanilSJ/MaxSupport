from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.models import User
from typing import List


async def create_user(session: AsyncSession, max_id: int) -> User:
    stmt = select(User).where(User.max_id == max_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        user = User(max_id=max_id)
        session.add(user)
        await session.commit()

    return user


async def get_all_users(session: AsyncSession) -> List[User]:
    stmt = select(User)
    result = await session.execute(stmt)
    users = result.scalars().all()
    return list(users)
