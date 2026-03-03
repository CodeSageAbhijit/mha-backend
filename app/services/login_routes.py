from bson import ObjectId
from fastapi import APIRouter, HTTPException, Form, status, Header, Request
from app.models.login_schemas import LoginUser, OTPRequest, OTPVerifyRequest
from app.database.mongo import psychiatrist_collection, counselor_collection, patient_collection, admin_collection, db, otp_collection, business_coach_collection, buddy_collection, mentor_collection
from app.utils.constants import verify_password, hash_password
from app.utils.jwt_tokens import create_access_token, create_refresh_token
from app.utils.encryption import encrypt_token
from app.models.token_schemas import TokenResponse
from datetime import datetime, timedelta
from pymongo.errors import PyMongoError
from app.models.login_schemas import ForgotPasswordRequest
from app.utils.jwt_tokens import create_password_reset_token
from app.utils.jwt_tokens import verify_password_reset_token
from app.models.login_schemas import ResetPasswordRequest
from jose import JWTError
from app.utils.email_utils import send_login_email, send_otp_email
from fastapi.responses import HTMLResponse
from jose import JWTError, ExpiredSignatureError
from pymongo.errors import PyMongoError
from app.utils.rate_limiter import limiter, RATE_LIMITS  # ✅ FIXED: Import rate limiter
import random
import string

from app.models.login_schemas import (
    LoginUser,
    ForgotPasswordRequest
)
from app.database.mongo import (
    psychiatrist_collection, counselor_collection, patient_collection,
    admin_collection, business_coach_collection, buddy_collection, mentor_collection,
)
from app.utils.constants import verify_password, hash_password
from app.utils.jwt_tokens import (
    create_access_token, create_refresh_token,
    create_password_reset_token, verify_password_reset_token,
    decrypt_token
)
from app.models.token_schemas import TokenData, LoginResponse
from app.utils.email_utils import send_login_email

import os
SECRET_KEY = os.getenv("SECRET_KEY", "6h2BPvHvCgJzit-9qeFlhi0_KrQ")
ALGORITHM = "HS256"

router = APIRouter(prefix="/api", tags=["Auth"])


# ✅ Uniform error response (normalized error string)
def _normalize_error_field(err):
    # If an HTTPException was passed, prefer its detail content
    if isinstance(err, HTTPException):
        detail = getattr(err, "detail", None)
        if isinstance(detail, dict):
            return detail.get("error") or detail.get("message") or str(detail)
        return str(detail) if detail is not None else str(err)

    # If a dict-like error was passed, try common keys
    if isinstance(err, dict):
        return err.get("error") or err.get("message") or str(err)

    # Fallback to string representation
    return str(err)

def error_response(status_code: int, message: str, error: str | dict | Exception, errors: list):
    normalized_error = _normalize_error_field(error)
    raise HTTPException(
        status_code=status_code,
        detail={
            "success": False,
            "status": status_code,
            "message": message,
            "data": None,
            "error": normalized_error,
            "errors": errors
        }
    )


# ✅ Uniform success response
def success_response(message: str, data=None):
    return {
        "success": True,
        "status": status.HTTP_200_OK,
        "message": message,
        "data": data,
        "error": None,
        "errors": []
    }


@router.post("/login", response_model=LoginResponse)
@limiter.limit(RATE_LIMITS["auth_login"])  # ✅ FIXED: Rate limit login to 10/minute
async def login(request: Request, user: LoginUser):
    try:
        print(f"🔍 DEBUG: Login attempt received")
        print(f"🔍 DEBUG: user object = {user}")
        print(f"🔍 DEBUG: user.username = {user.username}")
        print(f"🔍 DEBUG: user.role = {user.role}")
        print(f"🔍 DEBUG: user.password = {'*' * len(user.password)}")
        
        if not user.role or not user.username or not user.password:
            error_response(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Missing required fields",
                "Required fields: role, username, password",
                ["role, username, or password is missing"]
            )

        role = user.role.strip()
        username = user.username.lower().strip()
        password = user.password

        role_map = {
            "psychiatrist": psychiatrist_collection,
            "counselor": counselor_collection,
            "user": patient_collection,
            "admin": admin_collection,
            "business_coach": business_coach_collection,
            "buddy": buddy_collection,
            "mentor": mentor_collection,
        }
        collection = role_map.get(role)

        if collection is None:
            error_response(
                status.HTTP_400_BAD_REQUEST,
                "Invalid role provided",
                "Role not recognized",
                [f"Invalid role: {role}"]
            )

        # 🔹 Admin login logic
        if role == "admin":
            # Search by username OR email OR phone
            existing_admin = await collection.find_one({
                "$or": [
                    {"username": username},
                    {"email": username},
                    {"phoneNumber": username}
                ],
                "role": "admin"
            })
            
            if not existing_admin:
                error_response(
                    status.HTTP_401_UNAUTHORIZED,
                    "Invalid admin credentials",
                    "No admin account found",
                    ["Invalid admin username/password"]
                )
            
            if not verify_password(password, existing_admin["password"]):
                error_response(
                    status.HTTP_401_UNAUTHORIZED,
                    "Invalid admin credentials",
                    "Password is incorrect",
                    ["Invalid admin username/password"]
                )
            
            user_id = str(existing_admin["_id"])
            user_doc_id = existing_admin["_id"]
            admin_email = existing_admin.get("email", "admin@mha.com")

            token_payload = {"userId": user_id, "email": admin_email, "role": "admin"}
            access_token = create_access_token(token_payload)
            refresh_token = create_refresh_token(token_payload)

            await collection.update_one(
                {"_id": user_doc_id},
                {"$set": {"refreshToken": refresh_token, "lastLogin": datetime.utcnow()}}
            )

            return success_response(
                "Login successful",
                TokenData(
                    accessToken=access_token,
                    refreshToken=refresh_token,
                    userId=user_id,
                    role="admin"
                )
            )

        # 🔹 Normal login flow - Search by username OR email OR phone
        existing_user = await collection.find_one({
            "$or": [
                {"username": username},
                {"email": username},
                {"phoneNumber": username}
            ],
            "role": role
        })
        if not existing_user:
            error_response(
                status.HTTP_404_NOT_FOUND,
                "User not found",
                "No account matches the provided username and role",
                [f"No user found for username '{username}' and role '{role}'"]
            )

        if not verify_password(password, existing_user["password"]):
            error_response(
                status.HTTP_401_UNAUTHORIZED,
                "Incorrect password",
                "Password does not match our records",
                ["Invalid password"]
            )

        role_id_field = {
            "psychiatrist": "doctorId",
            "counselor": "counselorId",
            "user": "patientId",
            "business_coach": "businessCoachId",
            "buddy": "buddyId",
            "mentor": "mentorId",
        }.get(role)
        role_based_id = existing_user.get(role_id_field)

        token_payload = {
            "userId": str(existing_user["_id"]),
            "email": existing_user["email"],
            "role": role,
            "roleUserId": role_based_id
        }

        access_token = create_access_token(token_payload)
        refresh_token = create_refresh_token(token_payload)

        await collection.update_one(
            {"_id": existing_user["_id"]},
            {"$set": {"refreshToken": refresh_token, "lastLogin": datetime.utcnow()}}
        )

        return success_response(
            "Login successful",
            TokenData(
                accessToken=access_token,
                refreshToken=refresh_token,
                userId=token_payload["userId"],
                role=role,
                roleUserId=role_based_id
            )
        )

    except PyMongoError as e:
        error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Database error",
            str(e),
            ["MongoDB query failed"]
        )
    except HTTPException:
        raise
    except Exception as e:
        error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Unexpected error during login",
            str(e),
            ["Internal server error"]
        )


@router.post("/logout")
async def logout(authorization: str = Header(None, alias="Authorization")):
    try:
        if not authorization or not authorization.startswith("Bearer "):
            error_response(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Missing or invalid Authorization header",
                "Bearer refresh token not provided",
                ["Authorization header missing or invalid"]
            )

        refresh_token = authorization.split("Bearer ")[-1].strip()
        try:
            payload = decrypt_token(refresh_token)
            user_id = payload.get("userId")
            role = payload.get("role")

            if not user_id or not role:
                error_response(
                    status.HTTP_401_UNAUTHORIZED,
                    "Invalid token",
                    "Token payload missing required fields",
                    ["Invalid token format"]
                )

            collections = {
                "psychiatrist": psychiatrist_collection,
                "counselor": counselor_collection,
                "user": patient_collection,
                "admin": admin_collection,
                "business_coach": business_coach_collection,
                "buddy": buddy_collection,
                "mentor": mentor_collection,
            }
            collection = collections.get(role.lower())
            if collection is None:
                error_response(
                    status.HTTP_400_BAD_REQUEST,
                    "Invalid role",
                    f"Role {role} not recognized",
                    ["Invalid user role"]
                )

            result = await collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$unset": {"refreshToken": ""}}
            )

            if result.matched_count == 0:
                error_response(
                    status.HTTP_404_NOT_FOUND,
                    "User not found",
                    f"No {role} found with ID {user_id}",
                    ["User not found"]
                )

            return success_response("Logged out successfully", None)

        except Exception as e:
            error_response(
                status.HTTP_401_UNAUTHORIZED,
                "Invalid token",
                str(e),
                ["Token validation failed"]
            )

    except Exception as e:
        error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Logout failed",
            str(e),
            ["Unexpected error during logout"]
        )


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    try:
        user, _ = await find_user_by_email(request.email)
        if not user:
            error_response(
                status.HTTP_404_NOT_FOUND,
                "User not found",
                "No account registered with this email",
                [f"No user found with email '{request.email}'"]
            )

        token = create_password_reset_token(request.email)
        reset_link = f"http://127.0.0.1:8000/api/reset-password?token={token}"

        email_body = f"""
        Hello {user['firstName']},

        Click the link below to reset your password:
        {reset_link}

        This link will expire in 1 hour.
        """

        await send_login_email(
            to_email=request.email,
            name=user['firstName'],
            login_id="Password Reset Link",
            password=email_body
        )

        return success_response("Password reset link sent to your email", None)

    except Exception as e:
        error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Failed to send password reset link",
            str(e),
            ["Unexpected error in forgot-password"]
        )


async def find_user_by_email(email: str):
    for collection in [patient_collection, psychiatrist_collection, counselor_collection]:
        user = await collection.find_one({"email": email})
        if user:
            return user, collection
    return None, None


async def update_user_password(email: str, hashed_password: str):
    user, collection = await find_user_by_email(email)
    if not user:
        error_response(
            status.HTTP_404_NOT_FOUND,
            "User not found",
            "No account registered with this email",
            [f"No user found with email '{email}'"]
        )
    await collection.update_one({"email": email}, {"$set": {"password": hashed_password}})


@router.get("/reset-password", response_class=HTMLResponse)
async def show_reset_password_form(token: str):
    html_content = f"""
    <html>
        <body>
            <h2>Reset Password</h2>
            <form action="/api/reset-password" method="POST">
                <input type="hidden" name="token" value="{token}">
                <input type="password" name="new_password" placeholder="New Password" required>
                <input type="password" name="confirm_password" placeholder="Confirm Password" required>
                <button type="submit">Reset Password</button>
            </form>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.post("/reset-password")
async def reset_password(
    token: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...)
):
    try:
        if new_password != confirm_password:
            error_response(
                status.HTTP_400_BAD_REQUEST,
                "Password mismatch",
                "New password and confirm password do not match",
                ["Passwords do not match"]
            )

        email = verify_password_reset_token(token)
        if not email:
            error_response(
                status.HTTP_400_BAD_REQUEST,
                "Invalid or expired token",
                "Password reset link is invalid or expired",
                ["Invalid or expired token"]
            )

        hashed_password = hash_password(new_password)
        await update_user_password(email, hashed_password)

        return success_response("Password updated successfully", None)

    except Exception as e:
        error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Failed to reset password",
            str(e),
            ["Unexpected error in reset-password"]
        )


# ✅ OTP Helper Function
def generate_otp(length: int = 6) -> str:
    """Generate a random 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=length))


# ✅ OTP Request Endpoint
@router.post("/login/otp/request", response_model=dict)
@limiter.limit(RATE_LIMITS["auth_login"])  # Rate limit same as login
async def request_otp(request: Request, otp_req: OTPRequest):
    """
    Request OTP for login verification
    Step 1: User provides username, password, and role
    Step 2: Credentials validated, OTP sent to email
    """
    try:
        if not otp_req.role or not otp_req.username or not otp_req.password:
            error_response(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Missing required fields",
                "Required fields: role, username, password",
                ["role, username, or password is missing"]
            )

        role = otp_req.role.strip()
        username = otp_req.username.lower().strip()
        password = otp_req.password

        role_map = {
            "psychiatrist": psychiatrist_collection,
            "counselor": counselor_collection,
            "user": patient_collection,
            "admin": admin_collection,
            "business_coach": business_coach_collection,
            "buddy": buddy_collection,
            "mentor": mentor_collection,
        }
        collection = role_map.get(role)

        if collection is None:
            error_response(
                status.HTTP_400_BAD_REQUEST,
                "Invalid role provided",
                "Role not recognized",
                [f"Invalid role: {role}"]
            )

        # Find user by username, email, or phone
        existing_user = await collection.find_one({
            "$or": [
                {"username": username},
                {"email": username},
                {"phoneNumber": username}
            ],
            "role": role
        })

        if not existing_user:
            error_response(
                status.HTTP_404_NOT_FOUND,
                "User not found",
                "No account matches the provided username and role",
                [f"No user found for username '{username}' and role '{role}'"]
            )

        # Verify password
        if not verify_password(password, existing_user["password"]):
            error_response(
                status.HTTP_401_UNAUTHORIZED,
                "Incorrect password",
                "Password does not match our records",
                ["Invalid password"]
            )

        # Generate OTP
        otp = generate_otp()
        user_email = existing_user.get("email")
        user_name = existing_user.get("firstName", "User")

        # Store OTP in database with 10-minute expiry
        await otp_collection.insert_one({
            "username": username,
            "role": role,
            "userId": str(existing_user["_id"]),
            "otp": otp,
            "email": user_email,
            "createdAt": datetime.utcnow(),
            "expiresAt": datetime.utcnow() + timedelta(minutes=10),
            "isUsed": False
        })

        # Send OTP email
        email_sent = await send_otp_email(
            to_email=user_email,
            otp=otp,
            firstName=user_name
        )

        if not email_sent:
            error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Failed to send OTP",
                "Could not send OTP email",
                ["Email service error"]
            )

        return success_response(
            "OTP sent to your email",
            {
                "message": f"OTP sent to {user_email}",
                "expiresIn": 600  # 10 minutes in seconds
            }
        )

    except PyMongoError as e:
        error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Database error",
            str(e),
            ["MongoDB query failed"]
        )
    except HTTPException:
        raise
    except Exception as e:
        error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Unexpected error during OTP request",
            str(e),
            ["Internal server error"]
        )


# ✅ OTP Verify Endpoint
@router.post("/login/otp/verify", response_model=dict)
@limiter.limit("20/minute")  # Higher rate limit for verify attempts
async def verify_otp(request: Request, otp_verify: OTPVerifyRequest):
    """
    Verify OTP and return access/refresh tokens
    Step 2: User provides username, role, and OTP
    Step 3: OTP validated, tokens returned
    """
    try:
        if not otp_verify.role or not otp_verify.username or not otp_verify.otp:
            error_response(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Missing required fields",
                "Required fields: role, username, otp",
                ["role, username, or otp is missing"]
            )

        role = otp_verify.role.strip()
        username = otp_verify.username.lower().strip()
        otp = otp_verify.otp.strip()

        # Find OTP record
        otp_record = await otp_collection.find_one({
            "username": username,
            "role": role,
            "otp": otp,
            "isUsed": False,
            "expiresAt": {"$gt": datetime.utcnow()}
        })

        if not otp_record:
            error_response(
                status.HTTP_401_UNAUTHORIZED,
                "Invalid or expired OTP",
                "OTP is incorrect, expired, or already used",
                ["OTP verification failed"]
            )

        # Mark OTP as used
        await otp_collection.update_one(
            {"_id": otp_record["_id"]},
            {"$set": {"isUsed": True}}
        )

        # Get user data
        role_map = {
            "psychiatrist": psychiatrist_collection,
            "counselor": counselor_collection,
            "user": patient_collection,
            "admin": admin_collection,
            "business_coach": business_coach_collection,
            "buddy": buddy_collection,
            "mentor": mentor_collection,
        }
        collection = role_map.get(role)

        existing_user = await collection.find_one({"_id": ObjectId(otp_record["userId"])})

        if not existing_user:
            error_response(
                status.HTTP_404_NOT_FOUND,
                "User not found",
                "User account not found",
                ["User not found"]
            )

        # Get role-based ID
        role_id_field = {
            "psychiatrist": "doctorId",
            "counselor": "counselorId",
            "user": "patientId",
            "business_coach": "businessCoachId",
            "buddy": "buddyId",
            "mentor": "mentorId",
        }.get(role)
        role_based_id = existing_user.get(role_id_field)

        # Create tokens
        token_payload = {
            "userId": str(existing_user["_id"]),
            "email": existing_user["email"],
            "role": role,
            "roleUserId": role_based_id
        }

        access_token = create_access_token(token_payload)
        refresh_token = create_refresh_token(token_payload)

        # Update user with refresh token
        await collection.update_one(
            {"_id": existing_user["_id"]},
            {"$set": {"refreshToken": refresh_token, "lastLogin": datetime.utcnow()}}
        )

        # Clean up old OTPs for this user (optional)
        await otp_collection.delete_many({
            "userId": otp_record["userId"],
            "isUsed": True,
            "expiresAt": {"$lt": datetime.utcnow()}
        })

        return success_response(
            "Login successful",
            {
                "accessToken": access_token,
                "refreshToken": refresh_token,
                "userId": token_payload["userId"],
                "role": role,
                "roleUserId": role_based_id
            }
        )

    except PyMongoError as e:
        error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Database error",
            str(e),
            ["MongoDB query failed"]
        )
    except HTTPException:
        raise
    except Exception as e:
        return error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Unexpected error during OTP verification",
            str(e),
            ["Internal server error"]
        )
