import typing as t

from fastapi import FastAPI

from src.core.config import MainSettings, TestSettings
from src.lib import enums

from .dummies import (
    get_auth_user_id,
    get_domain_holder,
    get_github_sso,
    get_google_sso,
    get_is_editor,
    get_microsoft_sso,
    get_optional_auth_user_id,
    get_settings,
)

if t.TYPE_CHECKING:
    from src.injected import DomainHolder, SSOHolder


def setup_providers(
    *, app: FastAPI, domain_holder: "DomainHolder", sso_holder: "SSOHolder", settings: MainSettings | TestSettings
) -> None:
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_domain_holder] = lambda: domain_holder
    app.dependency_overrides[get_auth_user_id] = domain_holder.oauth.controller.get_auth_user_id(auto_error=True)
    app.dependency_overrides[get_optional_auth_user_id] = domain_holder.oauth.controller.get_auth_user_id(
        auto_error=False
    )
    app.dependency_overrides[get_google_sso] = lambda: sso_holder.google
    app.dependency_overrides[get_github_sso] = lambda: sso_holder.github
    app.dependency_overrides[get_microsoft_sso] = lambda: sso_holder.microsoft
    app.dependency_overrides[get_is_editor] = domain_holder.oauth.controller.get_access_provided(
        scope=enums.IAMScope.ADMIN_POSTS, access=enums.IAMAccess.READ, auto_error=False
    )
