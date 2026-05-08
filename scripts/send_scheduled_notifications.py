import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
from supabase import create_client


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
    name = user.get("name", "there")
    goal = user.get("goal", "maintenance")
    calories = user.get("daily_calories", "your")

    return (
        f"Hi {name},\n\n"
        "This is your automated NutriBot reminder.\n\n"
        f"Goal: {goal}\n"
        f"Daily calorie target: {calories} kcal\n\n"
        "Water reminder: drink a glass of water now.\n"
        "Meal reminder: choose a balanced meal from your NutriBot plan today.\n\n"
        "Regards,\nNutriBot"
    )


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
            "NutriBot Automated Water and Meal Reminder",
            build_reminder(user),
        )
        print(f"[NOTIFICATIONS] Sent reminder to {email}")


if __name__ == "__main__":
    main()
