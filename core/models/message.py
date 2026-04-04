from sqlalchemy import BigInteger, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class Message(Base):
    max_id: Mapped[int] = mapped_column(BigInteger)
    question: Mapped[bool] = mapped_column(Boolean)
    answer: Mapped[bool] = mapped_column(Boolean)