from typing import Optional

from sqlalchemy import BigInteger, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class User(Base):
    max_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    admin: Mapped[bool] = mapped_column(Boolean, default=False)

    chat_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("chats.id"),
        nullable=True
    )

    chat: Mapped[Optional["Chat"]] = relationship(back_populates="users")