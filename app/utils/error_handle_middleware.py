from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
import traceback, logging

logger = logging.getLogger("uvicorn.error")

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            # Log with traceback
            logger.error(f"Exception on {request.method} {request.url}", exc_info=exc)

            status_code = 500
            message = "Internal Server Error"
            error = str(exc)
            errors = []

            if isinstance(exc, HTTPException):
                status_code = exc.status_code
                message = exc.detail if isinstance(exc.detail, str) else "HTTP error"
                error = str(exc.detail)

            elif isinstance(exc, RequestValidationError):
                status_code = 422
                message = "Validation Error"
                error = "Invalid request"
                errors = exc.errors()

            return JSONResponse(
                status_code=status_code,
                content={
                    "success": False,
                    "statusCode": status_code,
                    "message": message,
                    "error": error,
                    "errors": errors,
                    "data": None,
                },
            )
