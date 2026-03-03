from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pymongo.errors import DuplicateKeyError, WriteError, OperationFailure, PyMongoError
import traceback

class MongoDBErrorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except DuplicateKeyError as e:
            traceback.print_exc()
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "statusCode": 400,
                    "message": "Duplicate key error in MongoDB",
                    "error": str(e),
                    "data": []
                }
            )
        except WriteError as e:
            traceback.print_exc()
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "statusCode": 400,
                    "message": "Write error in MongoDB",
                    "error": str(e),
                    "data": []
                }
            )
        except OperationFailure as e:
            traceback.print_exc()
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "statusCode": 500,
                    "message": "MongoDB operation failure",
                    "error": str(e),
                    "data": []
                }
            )
        except PyMongoError as e:
            traceback.print_exc()
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "statusCode": 500,
                    "message": "MongoDB error occurred",
                    "error": str(e),
                    "data": []
                }
            )
