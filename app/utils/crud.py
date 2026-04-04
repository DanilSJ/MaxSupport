from sqlalchemy.ext.asyncio import AsyncSession
from core.models import Message


async def create_message(
        session: AsyncSession,
        max_id: int,
        chat_id: int,
        answer: bool = False,
        question: bool = False,
) -> Message:
    message = Message(
        max_id=max_id,
        chat_id=chat_id,
        answer=answer,
        question=question
    )

    session.add(message)
    await session.commit()
    await session.refresh(message)

    return message