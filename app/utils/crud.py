from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.models import Message


async def create_message(
        session: AsyncSession,
        max_id: int,
        chat_id: int,
        admin_message_id: str | None,
        user_message_id: str,
        answer: bool = False,
        question: bool = False,
) -> Message:
    message = Message(
        max_id=max_id,
        chat_id=chat_id,
        admin_message_id=admin_message_id,
        user_message_id=user_message_id,
        answer=answer,
        question=question
    )

    session.add(message)
    await session.commit()
    await session.refresh(message)

    return message

async def get_message_by_admin_id(
        session: AsyncSession,
        admin_message_id: str
) -> Message | None:
    result = await session.execute(
        select(Message).where(Message.admin_message_id == admin_message_id)
    )
    return result.scalar_one_or_none()