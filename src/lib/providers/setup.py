import typing as t

from fastapi import FastAPI

from src.core.config import MainSettings
from src.lib import schemas

from .dummies import (
    get_auth_user_id,
    get_jwt_token_generation_info,
    get_s3_bucket_info,
)

if t.TYPE_CHECKING:
    from src.injected import DomainHolder


def setup_providers(*, app: FastAPI, domain_holder: "DomainHolder", settings: MainSettings) -> None:
    app.dependency_overrides[get_s3_bucket_info] = lambda: schemas.S3Bucket(
        name=settings.s3.bucket,
        endpoint=settings.s3.endpoint,
        replace_domain=settings.s3.replace_domain,
    )
    app.dependency_overrides[get_jwt_token_generation_info] = lambda: schemas.JwtTokenGenerationInfo(
        refresh_token_expires_minutes=settings.security.refresh_token_expire_minutes,
        access_token_expires_minutes=settings.security.access_token_expire_minutes,
        secret_key=settings.security.secret_key,
        sign_algorithm=settings.security.sign_algorithm,
    )
    app.dependency_overrides[get_auth_user_id] = lambda: domain_holder.oauth.controller.get_auth_user_id()
