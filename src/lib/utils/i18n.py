from src.lib import enums

DEFAULT_LANGUAGE = enums.LanguageType.ENGLISH


def get_accept_language_best_match(accept_language_header: str | None) -> enums.LanguageType:
    if not accept_language_header:
        return DEFAULT_LANGUAGE
    languages = accept_language_header.split(",")
    best_match = (str(DEFAULT_LANGUAGE), 0.0)

    for language in languages:
        if language.split(";")[0] == language:
            if language not in enums.LanguageType.choices():
                continue
            return enums.LanguageType(language)
        locale = language.split(";")[0].strip().split("-")[0]  # 'en-GB;q=0.9' -> 'en'
        q = float(language.split(";")[1].split("=")[1])  # 'en-GB;q=0.9' -> 0.9
        if locale in enums.LanguageType.choices() and q > best_match[1]:
            best_match = (locale, q)
    return enums.LanguageType(best_match[0])
