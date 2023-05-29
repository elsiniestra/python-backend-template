from .base import BaseEnum


class OffsetType(BaseEnum):
    FIRST = "first"
    NEXT = "next"
    SPECIFIC = "specific"
    PREV = "prev"
    LAST = "last"
