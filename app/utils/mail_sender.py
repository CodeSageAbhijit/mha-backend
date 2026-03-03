import aiosmtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
load_dotenv()

EMAIL_SENDER = "firewing.test@gmail.com"
EMAIL_PASSWORD = os.getenv("GOOGLE_APP_PASSWORD")  # Make sure this is a valid app password

async def send_login_email(*, to_email: str, name: str, login_id: str, password: str):
    subject = "Your Patient Portal Login Details"
    body = (
        f"Hello {name},\n\n"
        f"Your account has been created successfully.\n"
        f"Username: {login_id}\n"
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
        msg,   # ✅ positional
        hostname="smtp.gmail.com",
        port=587,
        start_tls=True,
        username=EMAIL_SENDER,
        password=EMAIL_PASSWORD,
)
        
        print(f"✅ Email sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {e}")
