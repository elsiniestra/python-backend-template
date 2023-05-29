class ReprMixin:
    """Class for automated `__repr__`"""

    def __repr__(self) -> str:
        return "<{}({})>".format(
            self.__class__.__name__,
            ", ".join(
                f"{attr}={repr(getattr(self, attr))}" for attr in filter(lambda x: not x.startswith("_"), self.__dict__)
            ),
        )
