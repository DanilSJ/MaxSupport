from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from core.models import User, Message


async def get_users_count(session: AsyncSession) -> int:
    stmt = select(func.count()).select_from(User)
    result = await session.execute(stmt)
    count = result.scalar_one()
    return count


async def get_user(session: AsyncSession, max_id: int) -> User | None:
    stmt = select(User).where(User.max_id == max_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_messages_stats(session: AsyncSession) -> tuple[int, int]:
    stmt_questions = select(func.count()).select_from(Message).where(Message.question == True)
    result_q = await session.execute(stmt_questions)
    questions_count = result_q.scalar_one()

    stmt_answers = select(func.count()).select_from(Message).where(Message.answer == True)
    result_a = await session.execute(stmt_answers)
    answers_count = result_a.scalar_one()

    return questions_count, answers_count