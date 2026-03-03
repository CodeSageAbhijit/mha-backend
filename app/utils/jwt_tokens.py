from datetime import datetime, timedelta
import os
import json
import base64
from dotenv import load_dotenv
from authlib.jose import JsonWebEncryption
from jose import jwt
# Load env vars
load_dotenv()

jwe = JsonWebEncryption()

header = {
    "alg": "dir",
    "enc": "A256CBC-HS512"
}

jwe_key_b64 = os.getenv("JWE_SECRET_KEY")
if not jwe_key_b64:
    raise ValueError("JWE_SECRET_KEY is missing from .env")

try:
    JWE_SECRET_KEY = base64.urlsafe_b64decode(jwe_key_b64)
    if len(JWE_SECRET_KEY) != 64:
        raise ValueError(f"JWE_SECRET_KEY must be 64 bytes. Got {len(JWE_SECRET_KEY)} bytes.")
except Exception as e:
    raise ValueError("Failed to decode JWE_SECRET_KEY") from e

# Create Access Token
def create_access_token(data: dict, expires_minutes: int = 1440) -> str:
    payload = data.copy()
    expire = datetime.now() + timedelta(minutes=expires_minutes)
    payload["exp"] = int(expire.timestamp())
    return jwe.serialize_compact(header, json.dumps(payload).encode(), JWE_SECRET_KEY)

# Create Refresh Token
def create_refresh_token(data: dict, expires_days: int = 7) -> str:
    payload = data.copy()
    expire = datetime.now() + timedelta(days=expires_days)
    payload["exp"] = int(expire.timestamp())
    return jwe.serialize_compact(header, json.dumps(payload).encode(), JWE_SECRET_KEY)

# Decrypt Token with Expiry Check
def decrypt_token(token: str) -> dict:
    try:
        #  First deserialize the compact token
        result = jwe.deserialize_compact(token, JWE_SECRET_KEY)

        #  Extract payload bytes
        decrypted_bytes = result['payload']

        #  Convert to dict
        payload = json.loads(decrypted_bytes.decode("utf-8"))
        print("Decrypted payload:", payload)

        return payload

    except Exception as e:
        print(" Token decryption error:", str(e))
        raise ValueError("Invalid or expired token") from e

SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")
ALGORITHM = "HS256"

def create_password_reset_token(email: str):
    expire = datetime.utcnow() + timedelta(hours=0.1)  # token expires in 1 hour
    payload = {"sub": email, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_password_reset_token(token: str):
    from jose.exceptions import JWTError, ExpiredSignatureError
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")  # returns the email
    except ExpiredSignatureError:
        return None
    except JWTError:
        return None