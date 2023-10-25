from .setup import setup_providers
from .dummies import (
    IsEditor,
    AuthUserId,
    OptionalAuthUserId,
    MainSettingsRequired,
    DomainHolderRequired,
    GoogleSSORequired,
    GithubSSORequired,
    MicrosoftSSORequired,
)


__all__ = [
    "setup_providers",
    "AuthUserId",
    "OptionalAuthUserId",
    "MainSettingsRequired",
    "DomainHolderRequired",
    "GithubSSORequired",
    "GoogleSSORequired",
    "MicrosoftSSORequired",
    "IsEditor",
]
