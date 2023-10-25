from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column


class ReprMixin:
    """Class for automated `__repr__`"""

    def __repr__(self) -> str:
        return "<{}({})>".format(
            self.__class__.__name__,
            ", ".join(
                f"{attr}={repr(getattr(self, attr))}" for attr in filter(lambda x: not x.startswith("_"), self.__dict__)
            ),
        )


class PKMixin:
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
