from fastapi import FastAPI


def create_app(*, is_production: bool) -> FastAPI:
    app: FastAPI = FastAPI(
        title="CatalanChess API",
        description="CatalanChess API",
        version="1.0.0",
        openapi_url="/openapi.json" if not is_production else None,
        docs_url="/docs" if not is_production else None,
        redoc_url="/redoc" if not is_production else None,
    )
    return app
