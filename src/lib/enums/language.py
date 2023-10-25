from .base import BaseEnum


# Note that enum value must be compatible with Accept-Language header
class LanguageType(str, BaseEnum):
    ENGLISH = "en"
    RUSSIAN = "ru"
