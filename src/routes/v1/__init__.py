from fastapi import FastAPI, HTTPException
from fastapi.responses import ORJSONResponse as JSONResponse
from pydantic import ValidationError

from const import SETTINGS, STORAGE
from generic import models as generic_models
from modules.error_handlers import (
    error_500_handler,
    generic_error_handler,
    validation_error_handler,
)

from . import resources

app_: FastAPI = FastAPI(
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

# -- ATTACH ROUTERS BELOW --
app_.include_router(resources.products.ROUTER)


@app_.get(
    "/", response_model=generic_models.BaseResponse, name="Healthcheck", tags=['Health']
)
async def _():
    """
    Check application health.
    """
    return generic_models.BaseResponse()
