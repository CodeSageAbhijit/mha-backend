from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from authlib.jose import JsonWebEncryption
import json
import base64
from dotenv import load_dotenv
import os

load_dotenv()

jwe = JsonWebEncryption()
jwe_key_b64 = os.getenv("JWE_SECRET_KEY")
if not jwe_key_b64:
    raise ValueError("JWE_SECRET_KEY is missing from .env")
JWE_SECRET_KEY = base64.urlsafe_b64decode(jwe_key_b64)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

# ✅ Utility: Decode JWE
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

import time
def decrypt_token(token: str):
    try:
        payload_bytes = jwe.deserialize_compact(token, JWE_SECRET_KEY)["payload"]
        payload = json.loads(payload_bytes.decode())
        print("Decoded payload:", payload)
        # Check expiry
        if "exp" in payload and int(payload["exp"]) < int(time.time()):
            print("Token expired:", payload["exp"])
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except Exception as e:
        print("Token decode error:", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(token: str = Depends(oauth2_scheme)):
    print(f"[DEBUG] Incoming Authorization token (first 20 chars): {token[:20]}...")
    try:
        payload = decrypt_token(token)
        print(f"[DEBUG] get_current_user payload: {payload}")
    except Exception as e:
        print(f"[ERROR] Token decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not payload:
        print("[ERROR] No payload after token decryption")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Ensure required fields are present
    if not payload.get("userId") or not payload.get("role"):
        print("❌ Missing userId or role in token payload")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing required fields",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


# ✅ Middleware-like dependency for admin-only routes
async def get_admin_user(request: Request, token: str = Depends(oauth2_scheme)):
    payload = decrypt_token(token)

    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin access is allowed"
        )

    # Attach user details to request
    request.state.user = payload
    return payload

