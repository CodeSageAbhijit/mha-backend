from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

def error_response(status_code: int, message: str, error: str, errors: list = None):
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "status": status_code,
            "message": message,
            "data": None,
            "error": error,
            "errors": errors or []
        }
    )

def format_pydantic_errors(exc: RequestValidationError):
    errs = []
    for err in exc.errors():
        loc = ".".join(str(l) for l in err.get("loc", []) if l != "body")
        errs.append({
            "field": loc,
            "message": err.get("msg", ""),
            "type": err.get("type", "value_error")
        })
    main_error = errs[0]["message"] if errs else "Validation error"
    return main_error, errs

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return error_response(
        status_code=exc.status_code,
        message=str(exc.detail),
        error=str(exc.detail),
        errors=[]
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    main_error, errs = format_pydantic_errors(exc)
    return error_response(
        status_code=400,  # 400 for bad request
        message=main_error,
        error=main_error,
        errors=errs
    )

async def generic_exception_handler(request: Request, exc: Exception):
    return error_response(
        status_code=500,
        message=str(exc),
        error=str(exc),
        errors=[]
    )
