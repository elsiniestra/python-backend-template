from typing import Any

from pydantic import BaseSettings as PydanticBaseSettings
from pydantic import Field, PostgresDsn, RedisDsn, validator


class AdminSettings(PydanticBaseSettings):
    username: str = Field(env="ADMIN_USERNAME")
    password: str = Field(env="ADMIN_PASSWORD")


class DBSettings(PydanticBaseSettings):
    pg_user: str = Field(env="POSTGRES_USER")
    pg_password: str = Field(env="POSTGRES_PASSWORD")
    pg_host: str = Field(env="POSTGRES_HOST")
    pg_port: str = Field(env="POSTGRES_PORT")
    pg_db: str = Field(env="POSTGRES_DB")
    pg_connection_url: str = Field(default=None)
    migrations_path: str = Field(default="migrations")

    @validator("pg_connection_url", pre=True)
    def assemble_db_connection(cls, value: str | None, values: dict[str, str]) -> Any:
        if value is not None:
            return value

        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            user=values.get("pg_user"),
            password=values.get("pg_password"),
            host=values.get("pg_host"),
            port=values.get("pg_port"),
            path=f"/{values.get('pg_db')}",
        )


class RedisSettings(PydanticBaseSettings):
    host: str = Field(env="REDIS_HOST", default="localhost")
    port: str = Field(env="REDIS_PORT", default="6379")
    connection_url: str = Field(default=None)
    iam_graph_name: str = Field(env="IAM_GRAPH_NAME", default="")
    graph_data_path: str = Field(env="GRAPH_DATA_PATH", default="")

    @validator("connection_url", pre=True)
    def assemble_db_connection(cls, value: str | None, values: dict[str, str]) -> Any:
        if value is not None:
            return value

        return RedisDsn.build(
            scheme="redis",
            host=values.get("host"),
            port=values.get("port"),
        )


class S3Settings(PydanticBaseSettings):
    bucket: str = Field(env="S3_BUCKET")
    replace_domain: str | None = Field(default=None, env="S3_REPLACE_DOMAIN")
    endpoint: str = Field(env="S3_ENDPOINT")
    access_key: str = Field(env="S3_ACCESS_KEY")
    secret_key: str = Field(env="S3_SECRET_KEY")
    region: str = Field(env="S3_REGION")


class CORSSettings(PydanticBaseSettings):
    allow_origins: list[str] = Field(env="ALLOW_ORIGINS")
    allow_methods: list[str] = Field(env="ALLOW_METHODS")
    allow_headers: list[str] = Field(env="ALLOW_HEADERS")
    allow_credentials: bool = Field(env="ALLOW_CREDENTIALS")


class EnvironmentSettings(PydanticBaseSettings):
    is_production: bool = Field(default=False, env="PRODUCTION")


class SecuritySettings(PydanticBaseSettings):
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_minutes: int = Field(default=60 * 24, env="REFRESH_TOKEN_EXPIRE_MINUTES")
    token_scheme: str = Field(default="Bearer", env="TOKEN_SCHEME")
    sign_algorithm: str = Field(default="HS256", env="SIGN_ALGORITHM")
    secret_key: str = Field(env="SECRET_KEY")


class ConfigPathSettings(PydanticBaseSettings):
    logger = Field(default="configs/logger.json")


class SentrySettings(PydanticBaseSettings):
    dsn: str | None = Field(default=None, env="SENTRY_DSN")
    traces_sample_rate: float = Field(default=1.0, env="TRACES_SAMPLE_RATE")


class MainSettings(PydanticBaseSettings):
    admin: AdminSettings
    db: DBSettings
    redis: RedisSettings
    s3: S3Settings
    cors: CORSSettings
    environment: EnvironmentSettings
    security: SecuritySettings
    config_path: ConfigPathSettings
    sentry: SentrySettings


class TestSettings(PydanticBaseSettings):
    admin: AdminSettings
    cors: CORSSettings
    environment: EnvironmentSettings
    security: SecuritySettings
    db: DBSettings
    redis: RedisSettings


def create_settings() -> MainSettings:
    return MainSettings(
        admin=AdminSettings(_env_file=".env"),
        db=DBSettings(_env_file=".env"),
        s3=S3Settings(_env_file=".env"),
        cors=CORSSettings(_env_file=".env"),
        environment=EnvironmentSettings(_env_file=".env"),
        security=SecuritySettings(_env_file=".env"),
        config_path=ConfigPathSettings(),
        redis=RedisSettings(_env_file=".env"),
        sentry=SentrySettings(_env_file=".env"),
    )


def create_test_settings() -> TestSettings:
    return TestSettings(
        admin=AdminSettings(username="admin", password="admin"),  # noqa: S106
        cors=CORSSettings(allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True),
        environment=EnvironmentSettings(is_production=False),
        security=SecuritySettings(  # noqa: S106
            access_token_expire_minutes=5,
            refresh_token_expire_minutes=10,
            sign_algorithm="SHA256",
            secret_key="superultratestsecretpassword",
        ),
        db=DBSettings(  # noqa: S106
            pg_user="testuser",
            pg_password="testpassword",
            pg_host="0.0.0.0",  # noqa: S104
            pg_port="5432",
            pg_db="testdb",
        ),
        redis=RedisSettings(host="0.0.0.0", port="6379"),
    )
