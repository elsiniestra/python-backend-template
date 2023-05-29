from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import MainSettings, TestSettings


def setup_middlewares(
    *,
    app: FastAPI,
    settings: MainSettings | TestSettings,
) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors.allow_origins,
        allow_credentials=settings.cors.allow_credentials,
        allow_methods=settings.cors.allow_methods,
        allow_headers=settings.cors.allow_headers,
    )
