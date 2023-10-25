from sqlalchemy import String
from sqlalchemy.orm import Mapped, column_property, mapped_column

from .base import PgBaseModel
from .mixins import PKMixin, ReprMixin


class User(PgBaseModel, PKMixin, ReprMixin):
    __tablename__ = "users"

    first_name: Mapped[str] = mapped_column(String(32), nullable=True)
    last_name: Mapped[str] = mapped_column(String(32), nullable=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = column_property(first_name + " " + last_name)
