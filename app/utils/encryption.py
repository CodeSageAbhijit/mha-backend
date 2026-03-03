from passlib.context import CryptContext
from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

# -------------------------------
# Load Fernet key
# -------------------------------
load_dotenv()
FERNET_SECRET = os.getenv("FERNET_SECRET")

if FERNET_SECRET is None:
    raise ValueError("FERNET_SECRET not found in .env")
FERNET_SECRET = FERNET_SECRET.encode()
fernet = Fernet(FERNET_SECRET)

def encrypt_token(token: str | bytes) -> str:
    if isinstance(token, str):
        token = token.encode()
    return fernet.encrypt(token).decode()

def decrypt_token(encrypted: str | bytes) -> str:
    if isinstance(encrypted, bytes):
        decrypted = fernet.decrypt(encrypted)
    elif isinstance(encrypted, str):
        decrypted = fernet.decrypt(encrypted.encode())
    else:
        raise ValueError("Invalid encrypted token type")
    return decrypted.decode()

# -------------------------------
# Password hashing utilities
# -------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a plain password"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)
