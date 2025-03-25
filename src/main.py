import asyncio
from contextlib import asynccontextmanager

import uvicorn
import uvloop
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse as JSONResponse
from pydantic import ValidationError

import routes
from const import ENVIRONMENT, ROOT_DIR, SETTINGS, STORAGE
from generic import models as generic_models
from modules import MigrationManager
from modules.error_handlers import (
    error_500_handler,
    generic_error_handler,
    validation_error_handler,
)

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


def migrate_db():
    """
    Apply DB migrations.
    """
    STORAGE.init_db()
    manager = MigrationManager(
        db_user=SETTINGS.db.user,
        db_password=SETTINGS.db.password,
        db_host=SETTINGS.db.host,
        db_name=SETTINGS.db.name,
        db_port=SETTINGS.db.port,
        base_dir=ROOT_DIR,
    )
    manager.apply()
    # Uncomment below for seeding
    # manager.set_migrations_dir("seeds")
    # manager.apply()


@asynccontextmanager  # pragma: no cover
async def lifespan(_: FastAPI):
    """
    App lifespan context manager
    :param _: Fastapi APP
    """
    # Startup
    await STORAGE.acquire_pool()
    yield  # pragma: no cover
    # Shutdown
    await STORAGE.close_pool()


app_: FastAPI = FastAPI(
    root_path=None if ENVIRONMENT in ("dev", "local") else "/api",
    lifespan=lifespan,
    docs_url=None if SETTINGS.disable_swagger_docs else "/docs",
    redoc_url=None if SETTINGS.disable_redoc_docs else "/redoc",
    title=SETTINGS.app.title,
    version=SETTINGS.app.version,
    default_response_class=JSONResponse,
    storage=STORAGE,
)

app_.add_exception_handler(500, error_500_handler)
app_.add_exception_handler(HTTPException, generic_error_handler)  # noqa
app_.add_exception_handler(ValidationError, validation_error_handler)  # noqa
app_.mount("/v1", routes.v1.app_, "V1")

app_.add_middleware(
    CORSMiddleware,  # noqa
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app_.get(
    "/", response_model=generic_models.BaseResponse, name="Healthcheck", tags=['Health']
)
async def _():
    """
    Check application health.
    """
    return generic_models.BaseResponse()


if __name__ == "__main__":  # pragma: no cover
    migrate_db()

    uvicorn.run(
        "main:app_",
        host=SETTINGS.app.host,
        port=SETTINGS.app.port,  # Local port to run at
        reload=ENVIRONMENT == "local",  # Enable file watchdog for local environment
        timeout_keep_alive=SETTINGS.app.keep_alive_timeout,
    )
