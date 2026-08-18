from fastapi import (
    FastAPI,
    Request,
)
from fastapi.exceptions import (
    RequestValidationError,
)
from fastapi.responses import (
    JSONResponse,
)
from starlette.exceptions import (
    HTTPException as StarletteHTTPException,
)


# =========================================================
# REGISTER ERROR HANDLERS
# =========================================================

def register_error_handlers(
    app: FastAPI,
) -> None:
    """
    Dhammaan API error handlers hal meel ka register garee.
    """

    # -----------------------------------------------------
    # VALIDATION ERROR
    # -----------------------------------------------------

    @app.exception_handler(
        RequestValidationError
    )
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:

        details = []

        for error in exc.errors():

            location = error.get(
                "loc",
                [],
            )

            field = None

            if location:
                field = str(
                    location[-1]
                )

            details.append(
                {
                    "field": field,
                    "message": error.get(
                        "msg",
                        "Invalid value.",
                    ),
                }
            )

        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": {
                    "type": "validation_error",
                    "message": (
                        "Request validation failed."
                    ),
                    "details": details,
                },
            },
        )

    # -----------------------------------------------------
    # HTTP EXCEPTION
    # -----------------------------------------------------

    @app.exception_handler(
        StarletteHTTPException
    )
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "type": "http_error",
                    "message": str(
                        exc.detail
                    ),
                    "details": None,
                },
            },
        )

    # -----------------------------------------------------
    # UNEXPECTED INTERNAL ERROR
    # -----------------------------------------------------

    @app.exception_handler(
        Exception
    )
    async def unexpected_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "type": "internal_server_error",
                    "message": (
                        "An unexpected server error occurred."
                    ),
                    "details": None,
                },
            },
        )