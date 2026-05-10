import os
import sys
import smtplib
import argparse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# FOR GITHUB ACTIONS IMPORTS
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from dotenv import load_dotenv
from supabase import create_client
from backend.services.notification_service import (
    build_daily_nutrition_guidance,
    get_water_reminder,
)


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


def send_daily_reminders(users):
    print(f"[NOTIFICATIONS] Sending daily nutrition guidance to {len(users)} users")
    for user in users:
        email = user.get("email")
        if not email:
            continue
        try:
            body = build_daily_nutrition_guidance(user)
            send_email(email, "NutriBot Daily Nutrition Guidance", body)
            print(f"[NOTIFICATIONS] Sent daily guidance to {email}")
        except Exception as e:
            print(f"[ERROR] Failed daily guidance for {email}: {e}")


def send_water_reminders(users):
    print(f"[NOTIFICATIONS] Sending water reminders to {len(users)} users")
    for user in users:
        email = user.get("email")
        name = user.get("name", "")
        if not email:
            continue
        try:
            body = (
                f"Dear {name},\n\n"
                "This is your hydration reminder from NutriBot.\n"
                "Please aim for regular water intake during the day "
                "(approximately 2 liters, unless advised otherwise by your clinician).\n\n"
                f"{get_water_reminder(name)}\n\n"
                "Sincerely,\nNutriBot Support"
            )
            send_email(email, "NutriBot Hydration Reminder", body)
            print(f"[NOTIFICATIONS] Sent water reminder to {email}")
        except Exception as e:
            print(f"[ERROR] Failed water reminder for {email}: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--type",
        choices=["daily", "water", "all"],
        default=os.getenv("NOTIFICATION_TYPE", "all"),
        help="Type of notification to send: daily, water, or all",
    )
    args = parser.parse_args()

    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_URL or SUPABASE_KEY is missing")

    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    response = client.table("users").select("*").execute()
    users = response.data or []

    print(f"[NOTIFICATIONS] Found {len(users)} users — type: {args.type}")

    if args.type in ("daily", "all"):
        send_daily_reminders(users)

    if args.type in ("water", "all"):
        send_water_reminders(users)


if __name__ == "__main__":
    main()
