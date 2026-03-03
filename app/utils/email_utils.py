import aiosmtplib
from email.mime.text import MIMEText
from datetime import datetime
from typing import Optional
import os

EMAIL_SENDER = "firewing.test@gmail.com"
EMAIL_PASSWORD = os.getenv("GOOGLE_APP_PASSWORD")

async def send_otp_email(
    *,
    to_email: str,
    otp: str,
    name: Optional[str] = None,
    firstName: Optional[str] = None,
):
    """Send OTP via email for login verification"""
    display_name = name or firstName or "User"

    subject = "Your OTP for Mental Health Assistant Login"
    body = (
        f"Hello {display_name},\n\n"
        f"Your One-Time Password (OTP) for login is:\n\n"
        f"🔐 {otp}\n\n"
        f"⏰ This OTP will expire in 10 minutes.\n"
        f"🔒 Never share this code with anyone.\n\n"
        "If you did not attempt to login, please ignore this email.\n\n"
        "Best regards,\n"
        "Mental Health Assistant Team"
    )
    msg = MIMEText(body)
    msg["From"] = EMAIL_SENDER
    msg["To"] = to_email
    msg["Subject"] = subject

    try:
        await aiosmtplib.send(
            msg,
            hostname="smtp.gmail.com",
            port=587,
            start_tls=True,
            username=EMAIL_SENDER,
            password=EMAIL_PASSWORD,
        )
        print(f"✅ OTP email sent to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send OTP email to {to_email}: {e}")
        return False


async def send_login_email(
    *,
    to_email: str,
    password: str,
    name: Optional[str] = None,
    firstName: Optional[str] = None,
    username: Optional[str] = None,
    login_id: Optional[str] = None,
):
    """Send login details email to the counselor. Accepts both (name, login_id) and (firstName, username)."""
    display_name = name or firstName or "User"
    display_login = username or login_id or "your account"

    subject = "Your Patient Portal Login Details"
    body = (
        f"Hello {display_name},\n\n"
        f"Your account has been created successfully.\n"
        f"Username: {display_login}\n"
        f"Password: {password}\n\n"
        "Please change your password after logging in for the first time.\n\n"
        "Best regards,\n"
        "Healthcare Admin Team"
    )
    msg = MIMEText(body)
    msg["From"] = EMAIL_SENDER
    msg["To"] = to_email
    msg["Subject"] = subject

    try:
        await aiosmtplib.send(
            msg,
            hostname="smtp.gmail.com",
            port=587,
            start_tls=True,
            username=EMAIL_SENDER,
            password=EMAIL_PASSWORD,
        )
        print(f"✅ Email sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {e}")
