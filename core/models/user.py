from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class User(Base):
    max_id: Mapped[int] = mapped_column(BigInteger, unique=True)