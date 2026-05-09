import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
from supabase import create_client
from backend.services.notification_service import build_daily_nutrition_guidance


load_dotenv()
load_dotenv("env", override=False)


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")


def send_email(to_email, subject, body):
    if not GMAIL_USER or not GMAIL_PASS:
        raise RuntimeError("GMAIL_USER or GMAIL_PASS is missing")

    message = MIMEMultipart()
    message["From"] = GMAIL_USER
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
        server.login(GMAIL_USER, GMAIL_PASS)
        server.send_message(message)


def build_reminder(user):
    return build_daily_nutrition_guidance(user)


def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_URL or SUPABASE_KEY is missing")

    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    response = client.table("users").select("*").execute()
    users = response.data or []

    print(f"[NOTIFICATIONS] Found {len(users)} users")
    for user in users:
        email = user.get("email")
        if not email:
            continue
        send_email(
            email,
            "NutriBot Daily Nutrition Guidance",
            build_reminder(user),
        )
        print(f"[NOTIFICATIONS] Sent reminder to {email}")


if __name__ == "__main__":
    main()
