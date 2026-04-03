from typing import List, Optional

from sqlalchemy import BigInteger, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class Chat(Base):
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    name: Mapped[str] = mapped_column(String)

    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("chats.id"),
        nullable=True
    )

    parent: Mapped[Optional["Chat"]] = relationship(
        remote_side="Chat.id",
        back_populates="children"
    )

    children: Mapped[List["Chat"]] = relationship(
        back_populates="parent"
    )

    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="chat"
    )
