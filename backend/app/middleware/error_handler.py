"""
Error handling middleware.
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from loguru import logger


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    logger.error(f"HTTP error: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "status": exc.status_code,
                "message": exc.detail,
                "path": str(request.url)
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "status": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "message": "Validation error",
                "details": exc.errors(),
                "path": str(request.url)
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal server error",
                "path": str(request.url)
            }
        }
    )


