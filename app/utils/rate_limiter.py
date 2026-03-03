"""
Rate limiting middleware to prevent abuse of auth endpoints and API attacks
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
from datetime import datetime

# Initialize rate limiter with skip OPTIONS for CORS preflight
limiter = Limiter(
    key_func=get_remote_address,
)

# Custom rate limit error handler
async def rate_limit_error_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors"""
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "status": 429,
            "message": "Too many requests",
            "data": None,
            "error": "Rate limit exceeded. Please try again later.",
            "errors": ["Too many requests from this IP address"],
            "timestamp": datetime.now().isoformat()
        }
    )

# Rate limit configurations
RATE_LIMITS = {
    "auth_login": "10/minute",           # Max 10 login attempts per minute
    "auth_register": "5/minute",         # Max 5 registrations per minute
    "password_reset": "3/minute",        # Max 3 password reset requests per minute
    "general_api": "100/minute",         # Max 100 general API calls per minute
    "chat_message": "30/minute",         # Max 30 chat messages per minute
    "call_initiate": "5/minute",         # Max 5 call initiations per minute
}
