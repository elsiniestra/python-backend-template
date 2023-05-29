from sqlalchemy import Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class PgBaseModel(DeclarativeBase):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, nullable=False)
