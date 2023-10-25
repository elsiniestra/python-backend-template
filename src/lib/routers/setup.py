from fastapi import APIRouter, FastAPI

from src.injected import DomainHolder
from src.lib.routers.v1 import create_v1_router


def setup_routers(app: FastAPI, domain_holder: DomainHolder) -> None:
    main_router: APIRouter = create_v1_router(domain_holder=domain_holder)
    app.include_router(main_router)


__all__ = ["setup_routers"]
