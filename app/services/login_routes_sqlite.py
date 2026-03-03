"""
SQLite Login Routes - Replaces MongoDB-based login
Uses SQLAlchemy ORM instead of Motor/PyMongo
"""

from fastapi import APIRouter, HTTPException, Form, status, Header, Request, Depends
from sqlalchemy.orm import Session
from app.models.login_schemas import LoginUser, OTPRequest, OTPVerifyRequest, ForgotPasswordRequest, ResetPasswordRequest
from app.database.database import get_db
from app.models.sqlite_models import User, Patient, Psychiatrist, Counselor, Admin, OTP
from app.utils.constants import verify_password, hash_password
from app.utils.jwt_tokens import create_access_token, create_refresh_token, verify_password_reset_token, create_password_reset_token, decrypt_token
from app.models.token_schemas import TokenData, LoginResponse
from app.utils.email_utils import send_login_email, send_otp_email
from app.utils.rate_limiter import limiter, RATE_LIMITS
from datetime import datetime, timedelta
from fastapi.responses import HTMLResponse
import random
import string
import uuid

router = APIRouter(prefix="/api", tags=["Auth"])

def generate_id():
    """Generate unique ID"""
    return str(uuid.uuid4())

def generate_otp(length: int = 6) -> str:
    """Generate a random 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=length))

def _normalize_error_field(err):
    """Normalize error field"""
    if isinstance(err, HTTPException):
        detail = getattr(err, "detail", None)
        if isinstance(detail, dict):
            return detail.get("error") or detail.get("message") or str(detail)
        return str(detail) if detail is not None else str(err)
    
    if isinstance(err, dict):
        return err.get("error") or err.get("message") or str(err)
    
    return str(err)

def error_response(status_code: int, message: str, error: str | dict | Exception, errors: list):
    """Standardized error response"""
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

def success_response(message: str, data=None):
    """Standardized success response"""
    return {
        "success": True,
        "status": status.HTTP_200_OK,
        "message": message,
        "data": data,
        "error": None,
        "errors": []
    }

# ✅ Regular Login Endpoint
@router.post("/login", response_model=LoginResponse)
@limiter.limit(RATE_LIMITS["auth_login"])
async def login(request: Request, user: LoginUser, db: Session = Depends(get_db)):
    """
    Login with username/email/phone and password
    """
    try:
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

        # Find user by username, email, or phone
        existing_user = db.query(User).filter(
            (User.username == username) | 
            (User.email == username) | 
            (User.phoneNumber == username),
            User.role == role
        ).first()

        if not existing_user:
            error_response(
                status.HTTP_404_NOT_FOUND,
                "User not found",
                "No account matches the provided username and role",
                [f"No user found for username '{username}' and role '{role}'"]
            )

        if not verify_password(password, existing_user.password):
            error_response(
                status.HTTP_401_UNAUTHORIZED,
                "Incorrect password",
                "Password does not match our records",
                ["Invalid password"]
            )

        # Get role-based ID
        role_based_id = None
        if role == "user":
            patient = db.query(Patient).filter(Patient.userId == existing_user.id).first()
            role_based_id = patient.patientId if patient else None
        elif role == "psychiatrist":
            doctor = db.query(Psychiatrist).filter(Psychiatrist.userId == existing_user.id).first()
            role_based_id = doctor.doctorId if doctor else None
        elif role == "counselor":
            counselor = db.query(Counselor).filter(Counselor.userId == existing_user.id).first()
            role_based_id = counselor.counselorId if counselor else None

        # Create tokens
        token_payload = {
            "userId": existing_user.id,
            "email": existing_user.email,
            "role": role,
            "roleUserId": role_based_id
        }

        access_token = create_access_token(token_payload)
        refresh_token = create_refresh_token(token_payload)

        # Update refresh token and last login
        existing_user.refreshToken = refresh_token
        existing_user.lastLogin = datetime.utcnow()
        db.commit()

        return success_response(
            "Login successful",
            TokenData(
                accessToken=access_token,
                refreshToken=refresh_token,
                userId=existing_user.id,
                role=role,
                roleUserId=role_based_id
            )
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


# ✅ OTP Request Endpoint
@router.post("/login/otp/request", response_model=dict)
@limiter.limit(RATE_LIMITS["auth_login"])
async def request_otp(request: Request, otp_req: OTPRequest, db: Session = Depends(get_db)):
    """
    Request OTP for login verification
    Step 1: Validate credentials and send OTP
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

        # Find user
        existing_user = db.query(User).filter(
            (User.username == username) | 
            (User.email == username) | 
            (User.phoneNumber == username),
            User.role == role
        ).first()

        if not existing_user:
            error_response(
                status.HTTP_404_NOT_FOUND,
                "User not found",
                "No account matches the provided username and role",
                [f"No user found for username '{username}' and role '{role}'"]
            )

        # Verify password
        if not verify_password(password, existing_user.password):
            error_response(
                status.HTTP_401_UNAUTHORIZED,
                "Incorrect password",
                "Password does not match our records",
                ["Invalid password"]
            )

        # Generate OTP
        otp = generate_otp()
        user_email = existing_user.email
        user_name = existing_user.firstName

        # Store OTP with 10-minute expiry
        otp_record = OTP(
            id=generate_id(),
            username=username,
            role=role,
            userId=existing_user.id,
            otp=otp,
            email=user_email,
            createdAt=datetime.utcnow(),
            expiresAt=datetime.utcnow() + timedelta(minutes=10),
            isUsed=False
        )
        db.add(otp_record)
        db.commit()

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
@limiter.limit("20/minute")
async def verify_otp(request: Request, otp_verify: OTPVerifyRequest, db: Session = Depends(get_db)):
    """
    Verify OTP and return tokens
    Step 2: Validate OTP and issue tokens
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

        # Find valid OTP
        otp_record = db.query(OTP).filter(
            OTP.username == username,
            OTP.role == role,
            OTP.otp == otp,
            OTP.isUsed == False,
            OTP.expiresAt > datetime.utcnow()
        ).first()

        if not otp_record:
            error_response(
                status.HTTP_401_UNAUTHORIZED,
                "Invalid or expired OTP",
                "OTP is incorrect, expired, or already used",
                ["OTP verification failed"]
            )

        # Mark OTP as used
        otp_record.isUsed = True
        db.commit()

        # Get user data
        existing_user = db.query(User).filter(User.id == otp_record.userId).first()

        if not existing_user:
            error_response(
                status.HTTP_404_NOT_FOUND,
                "User not found",
                "User account not found",
                ["User not found"]
            )

        # Get role-based ID
        role_based_id = None
        if role == "user":
            patient = db.query(Patient).filter(Patient.userId == existing_user.id).first()
            role_based_id = patient.patientId if patient else None
        elif role == "psychiatrist":
            doctor = db.query(Psychiatrist).filter(Psychiatrist.userId == existing_user.id).first()
            role_based_id = doctor.doctorId if doctor else None
        elif role == "counselor":
            counselor = db.query(Counselor).filter(Counselor.userId == existing_user.id).first()
            role_based_id = counselor.counselorId if counselor else None

        # Create tokens
        token_payload = {
            "userId": existing_user.id,
            "email": existing_user.email,
            "role": role,
            "roleUserId": role_based_id
        }

        access_token = create_access_token(token_payload)
        refresh_token = create_refresh_token(token_payload)

        # Update refresh token and last login
        existing_user.refreshToken = refresh_token
        existing_user.lastLogin = datetime.utcnow()
        db.commit()

        # Clean up old used OTPs
        db.query(OTP).filter(
            OTP.userId == otp_record.userId,
            OTP.isUsed == True,
            OTP.expiresAt < datetime.utcnow()
        ).delete()
        db.commit()

        return success_response(
            "Login successful",
            {
                "accessToken": access_token,
                "refreshToken": refresh_token,
                "userId": existing_user.id,
                "role": role,
                "roleUserId": role_based_id
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Unexpected error during OTP verification",
            str(e),
            ["Internal server error"]
        )


# ✅ Logout Endpoint
@router.post("/logout")
async def logout(authorization: str = Header(None, alias="Authorization"), db: Session = Depends(get_db)):
    """Logout and invalidate refresh token"""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            error_response(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Missing or invalid Authorization header",
                "Bearer token not provided",
                ["Authorization header missing or invalid"]
            )

        refresh_token = authorization.split("Bearer ")[-1].strip()
        try:
            payload = decrypt_token(refresh_token)
            user_id = payload.get("userId")

            if not user_id:
                error_response(
                    status.HTTP_401_UNAUTHORIZED,
                    "Invalid token",
                    "Token payload missing required fields",
                    ["Invalid token format"]
                )

            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                error_response(
                    status.HTTP_404_NOT_FOUND,
                    "User not found",
                    f"No user found with ID {user_id}",
                    ["User not found"]
                )

            user.refreshToken = None
            db.commit()

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


# ✅ Forgot Password Endpoint
@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Send password reset link to email"""
    try:
        user = db.query(User).filter(User.email == request.email).first()
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
        Hello {user.firstName},

        Click the link below to reset your password:
        {reset_link}

        This link will expire in 1 hour.
        """

        await send_login_email(
            to_email=request.email,
            name=user.firstName,
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


# ✅ Reset Password Form
@router.get("/reset-password", response_class=HTMLResponse)
async def show_reset_password_form(token: str):
    """Show password reset form"""
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


# ✅ Reset Password Endpoint  
@router.post("/reset-password")
async def reset_password(
    token: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Reset password with token"""
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

        user = db.query(User).filter(User.email == email).first()
        if not user:
            error_response(
                status.HTTP_404_NOT_FOUND,
                "User not found",
                "No account registered with this email",
                [f"No user found with email '{email}'"]
            )

        hashed_password = hash_password(new_password)
        user.password = hashed_password
        db.commit()

        return success_response("Password updated successfully", None)

    except Exception as e:
        error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Failed to reset password",
            str(e),
            ["Unexpected error in reset-password"]
        )
