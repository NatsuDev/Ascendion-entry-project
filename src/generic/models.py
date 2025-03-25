from pydantic import BaseModel, Field, model_validator


class BaseResponse(BaseModel):
    """
    Successful base response.
    """

    ok: bool = Field(
        default=True, title="OK", description="Whether the request was successful"
    )


class BasePaginatedResponse(BaseResponse):
    """
    Successful base paginated response.
    """

    page: int = Field(title="Page number", description="Page number")
    items_per_page: int = Field(
        title="Number of items per page", description="Number of items per page"
    )
    total_pages: int = Field(
        title="Total number of pages", description="Total number of pages"
    )


class BaseErrorResponse(BaseResponse):
    """
    Error response, where either `message` or `traceback` must be filled for the response to be valid.
    """

    ok: bool = Field(
        default=False, title="OK", description="Whether the request was successful"
    )
    message: str | None = Field(
        default=None, title="Error message", description="Error description"
    )
    traceback: list[str] | None = Field(
        default=None, title="Error traceback", description="Error traceback"
    )

    @model_validator(mode="before")
    @classmethod
    def _(cls, data):
        """
        Validates that either `message` or `traceback` is provided.
        :param data: Object values.
        :return: Unmodified object values.
        """
        if data.get("message") is None and data.get("traceback") is None:
            raise ValueError("Either `message` or `traceback` must be provided")
        return data


class Error404Response(BaseErrorResponse):  # Not found
    """
    The server cannot find the requested resource. In the browser, this means the URL is not recognized.
    In an API, this can also mean that the endpoint is valid but the resource itself does not exist.
    Servers may also send this response instead of 403 Forbidden to hide the existence of a resource from an
    unauthorized client. This response code is probably the most well known due to its frequent occurrence on the web.
    https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404.
    """

    message: str = "Not found"


class Error422Response(BaseErrorResponse):  # Unprocessable Content
    """
    Indicates that the server understood the content type of the request content,
    and the syntax of the request content was correct,
    but it was unable to process the contained instructions.
    https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/422.
    """

    message: str = "Unprocessable Content"


class Error500Response(BaseErrorResponse):  # Internal server error
    """
    The server has encountered a situation it does not know how to handle.
    https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/500.
    """

    message: str = "Internal server error"
