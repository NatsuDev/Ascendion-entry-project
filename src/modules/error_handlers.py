import traceback

from fastapi import HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import ORJSONResponse as JSONResponse
from pydantic import ValidationError

from generic import models as generic_models


async def generic_error_handler(_: Request, exc: HTTPException):
    """
    FastAPI error handler.
    :param _: FastAPI Request.
    :param exc: FastAPI HTTPException.
    :return: Respective error class.
    """
    exc_class = getattr(generic_models, f"Error{exc.status_code}Response", None)
    if exc_class:
        kwargs = {"ok": False}
        if exc.detail:
            kwargs["message"] = exc.detail
    else:
        exc_class = generic_models.BaseErrorResponse
        kwargs = {
            "message": exc.detail
            or "No description, you should report this error to developers."
        }
    return JSONResponse(
        jsonable_encoder(exc_class(**kwargs)),
        status_code=exc.status_code,
        headers=exc.headers,
    )


async def validation_error_handler(_: Request, exc: ValidationError):
    """
    Pydantic validation error handler.
    :param _: FastAPI Request.
    :param exc: ValidationError object.
    :return: 422 error class.
    """
    return JSONResponse(
        jsonable_encoder(
            generic_models.Error422Response(
                message='Validation Error', traceback=str(exc).split('\n')
            )
        ),
        status_code=422,
    )


async def error_500_handler(_: Request, __: Exception):
    """
    Python error handler that transforms exceptions to 500.
    :param _: FastAPI Request.
    :param __: Any Exception.
    :return: Respective error class.
    """
    response_body = generic_models.Error500Response(
        message="You encountered an internal error. Report your HTTP request and value of `traceback` to developer.",
        traceback=traceback.format_exc().strip().replace('"', "`").split("\n"),
    )

    return JSONResponse(jsonable_encoder(response_body), status_code=500)
