import enum
from typing import Any


class BaseEnumMeta(enum.EnumMeta):
    def __contains__(cls, string: object) -> bool:
        try:
            cls(string)  # check is there is the element in Enum
        except ValueError:
            return False
        else:
            return True


class BaseEnum(enum.Enum, metaclass=BaseEnumMeta):
    def __eq__(self, member: Any) -> bool:
        result: bool = member == self.value
        return result

    def __str__(self) -> str:
        return str(self._value_)

    def __repr__(self) -> str:
        return self.__str__()

    def __hash__(self) -> int:
        return hash(self._name_)

    @classmethod
    def choices(cls) -> list[Any]:
        return [i.value for i in cls]
