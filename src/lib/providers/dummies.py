from typing import TYPE_CHECKING, Annotated

from fastapi import Depends
from fastapi_sso.sso.github import GithubSSO
from fastapi_sso.sso.google import GoogleSSO
from fastapi_sso.sso.microsoft import MicrosoftSSO

from src.core.config import MainSettings

if TYPE_CHECKING:
    from src.injected import DomainHolder


def get_auth_user_id() -> int:  # type: ignore
    pass


def get_optional_auth_user_id() -> int:  # type: ignore
    pass


def get_settings() -> MainSettings:  # type: ignore
    pass


def get_domain_holder() -> "DomainHolder":  # type: ignore
    pass


def get_google_sso() -> GoogleSSO:
    pass


def get_github_sso() -> GithubSSO:
    pass


def get_microsoft_sso() -> MicrosoftSSO:
    pass


def get_is_editor() -> bool:  # type: ignore
    pass


AuthUserId = Annotated[int, Depends(get_auth_user_id)]
OptionalAuthUserId = Annotated[int, Depends(get_optional_auth_user_id)]
IsEditor = Annotated[bool, Depends(get_is_editor)]
MainSettingsRequired = Annotated[MainSettings, Depends(get_settings)]
DomainHolderRequired = Annotated["DomainHolder", Depends(get_domain_holder)]
GoogleSSORequired = Annotated[GoogleSSO, Depends(get_google_sso)]
GithubSSORequired = Annotated[GithubSSO, Depends(get_github_sso)]
MicrosoftSSORequired = Annotated[MicrosoftSSO, Depends(get_microsoft_sso)]
