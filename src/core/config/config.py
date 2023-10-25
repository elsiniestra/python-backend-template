from typing import Any

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_core.core_schema import FieldValidationInfo
from pydantic_settings import BaseSettings as PydanticBaseSettings
from pydantic_settings import SettingsConfigDict


class BaseEnvSettings(PydanticBaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class AdminSettings(BaseEnvSettings):
    username: str = Field(validation_alias="ADMIN_USERNAME")
    password: str = Field(validation_alias="ADMIN_PASSWORD")


class DBSettings(BaseEnvSettings):
    pg_user: str = Field(validation_alias="POSTGRES_USER")
    pg_password: str = Field(validation_alias="POSTGRES_PASSWORD")
    pg_host: str = Field(validation_alias="POSTGRES_HOST")
    pg_port: int = Field(validation_alias="POSTGRES_PORT")
    pg_db: str = Field(validation_alias="POSTGRES_DB")
    pg_connection_url: str | None = Field(default=None)
    migrations_path: str = Field(default="migrations")

    @field_validator("pg_connection_url", mode="after")
    def assemble_db_connection(cls, value: str | None, info: FieldValidationInfo) -> Any:
        if value is not None:
            return value

        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=info.data.get("pg_user"),
                password=info.data.get("pg_password"),
                host=info.data.get("pg_host"),
                port=info.data.get("pg_port"),
                path=info.data.get("pg_db"),
            )
        )


class RedisSettings(BaseEnvSettings):
    host: str = Field(validation_alias="REDIS_HOST")
    port: int = Field(validation_alias="REDIS_PORT")
    connection_url: str | None = Field(default=None)
    iam_graph_name: str = Field(validation_alias="IAM_GRAPH_NAME")
    graph_data_path: str = Field(validation_alias="GRAPH_DATA_PATH")

    @field_validator("connection_url", mode="after")
    def assemble_db_connection(cls, value: str | None, info: FieldValidationInfo) -> Any:
        if value is not None:
            return value

        return str(
            RedisDsn.build(
                scheme="redis",
                host=info.data.get("host"),
                port=info.data.get("port"),
            )
        )


class S3Settings(BaseEnvSettings):
    bucket: str = Field(validation_alias="S3_BUCKET")
    replace_domain: str | None = Field(default=None, validation_alias="S3_REPLACE_DOMAIN")
    endpoint: str = Field(validation_alias="S3_ENDPOINT")
    access_key: str = Field(validation_alias="S3_ACCESS_KEY")
    secret_key: str = Field(validation_alias="S3_SECRET_KEY")
    region: str = Field(validation_alias="S3_REGION")


class CORSSettings(BaseEnvSettings):
    allow_origins: list[str] = Field(validation_alias="ALLOW_ORIGINS")
    allow_methods: list[str] = Field(validation_alias="ALLOW_METHODS")
    allow_headers: list[str] = Field(validation_alias="ALLOW_HEADERS")
    allow_credentials: bool = Field(validation_alias="ALLOW_CREDENTIALS")


class EnvironmentSettings(BaseEnvSettings):
    is_production: bool = Field(default=False, validation_alias="PRODUCTION")
    is_testing: bool = Field(default=False, validation_alias="TESTING")


class SecuritySettings(BaseEnvSettings):
    access_token_expires_minutes: int = Field(default=30, validation_alias="ACCESS_TOKEN_EXPIRES_MINUTES")
    refresh_token_expires_minutes: int = Field(default=60 * 24, validation_alias="REFRESH_TOKEN_EXPIRES_MINUTES")
    token_scheme: str = Field(default="Bearer", validation_alias="TOKEN_SCHEME")
    sign_algorithm: str = Field(default="HS256", validation_alias="SIGN_ALGORITHM")
    secret_key: str = Field(validation_alias="SECRET_KEY")


class ConfigPathSettings(BaseEnvSettings):
    logger: str = Field(default="configs/logger.json")


class SentrySettings(BaseEnvSettings):
    dsn: str | None = Field(default=None, validation_alias="SENTRY_DSN")
    traces_sample_rate: float = Field(default=1.0, validation_alias="TRACES_SAMPLE_RATE")


class GoogleSSOSettings(BaseEnvSettings):
    client_id: str = Field(validation_alias="GOOGLE_CLIENT_ID")
    client_secret: str = Field(validation_alias="GOOGLE_CLIENT_SECRET")
    redirect_uri: str = Field(validation_alias="GOOGLE_REDIRECT_URI")


class GithubSSOSettings(BaseEnvSettings):
    client_id: str = Field(validation_alias="GITHUB_CLIENT_ID")
    client_secret: str = Field(validation_alias="GITHUB_CLIENT_SECRET")
    redirect_uri: str = Field(validation_alias="GITHUB_REDIRECT_URI")


class MicrosoftSSOSettings(BaseEnvSettings):
    client_id: str = Field(validation_alias="MICROSOFT_CLIENT_ID")
    client_secret: str = Field(validation_alias="MICROSOFT_CLIENT_SECRET")
    tenant: str = Field(validation_alias="MICROSOFT_REDIRECT_URI")
    redirect_uri: str = Field(validation_alias="MICROSOFT_REDIRECT_URI")


class SSOSettings(BaseEnvSettings):
    google: GoogleSSOSettings = GoogleSSOSettings()
    github: GithubSSOSettings = GithubSSOSettings()
    microsoft: MicrosoftSSOSettings = MicrosoftSSOSettings()


class MainSettings(BaseEnvSettings):
    admin: AdminSettings
    db: DBSettings
    redis: RedisSettings
    s3: S3Settings
    cors: CORSSettings
    environment: EnvironmentSettings
    security: SecuritySettings
    config_path: ConfigPathSettings
    sentry: SentrySettings
    sso: SSOSettings


class TestSettings(BaseEnvSettings):
    admin: AdminSettings
    cors: CORSSettings
    environment: EnvironmentSettings
    security: SecuritySettings
    db: DBSettings
    redis: RedisSettings
    config_path: ConfigPathSettings


def create_settings() -> MainSettings:
    return MainSettings(
        admin=AdminSettings(),
        db=DBSettings(),
        s3=S3Settings(),
        cors=CORSSettings(),
        environment=EnvironmentSettings(),
        security=SecuritySettings(),
        config_path=ConfigPathSettings(),
        redis=RedisSettings(),
        sentry=SentrySettings(),
        sso=SSOSettings(),
    )


def create_test_settings() -> TestSettings:
    return TestSettings(
        admin=AdminSettings(username="admin", password="admin"),  # noqa: S106
        db=DBSettings(),
        cors=CORSSettings(allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True),
        environment=EnvironmentSettings(is_production=False),
        security=SecuritySettings(  # noqa: S106
            access_token_expires_minutes=5,
            refresh_token_expires_minutes=10,
            sign_algorithm="HS256",
            secret_key="superultratestsecretpassword",
        ),
        config_path=ConfigPathSettings(),
        redis=RedisSettings(),
    )
