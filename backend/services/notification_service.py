import smtplib
import time
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    import schedule
except ImportError:
    schedule = None

from backend.config import GMAIL_USER, GMAIL_PASS
from supabase import create_client
from backend.config import SUPABASE_URL, SUPABASE_KEY
from groq import Groq
from backend.config import GROQ_API_KEY


def _get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def _get_groq_client():
    return Groq(api_key=GROQ_API_KEY)


def get_water_reminder(name: str = "") -> str:
    display_name = str(name).strip()
    if display_name:
        return f"Hi {display_name}, don't forget to drink a glass of water to stay hydrated."
    return "Don't forget to drink a glass of water to stay hydrated."


def send_email(to_email, subject, body):
    print(f"[EMAIL] Preparing email to {to_email} with subject: {subject}", flush=True)
    if not GMAIL_USER or not GMAIL_PASS:
        message = "Email failed: GMAIL_USER or GMAIL_PASS is missing."
        print(f"[EMAIL] {message}", flush=True)
        return False, message

    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=20)
        server.login(GMAIL_USER, GMAIL_PASS)
        server.send_message(msg)
        server.quit()
        print(f"[EMAIL] Email sent to {to_email}", flush=True)
        return True, f"Email sent to {to_email}"
    except Exception as e:
        message = f"Email failed: {e}"
        print(f"[EMAIL] {message}", flush=True)
        return False, message


def send_demo_notification(user: dict):
    name = user.get("name", "there")
    goal = user.get("goal", "maintenance")
    calories = user.get("daily_calories", "your")
    body = (
        f"Hi {name},\n\n"
        "This is your NutriBot demo notification.\n"
        f"Goal: {goal}\n"
        f"Daily calorie target: {calories} kcal\n\n"
        "Water reminder: please drink a glass of water now.\n"
        "Meal reminder: check your NutriBot meal plan and choose a balanced meal for your goal.\n\n"
        "Regards,\nNutriBot"
    )
    return send_email(user["email"], "NutriBot Water and Meal Reminder", body)


def send_registration_notification(user: dict):
    name = user.get("name", "there")
    goal = user.get("goal", "maintenance")
    calories = user.get("daily_calories", "your")
    bmi = user.get("bmi", "N/A")
    bmi_category = user.get("bmi_category", "N/A")

    body = (
        f"Hi {name},\n\n"
        "Welcome to NutriBot! Your profile has been registered successfully.\n\n"
        f"Goal: {goal}\n"
        f"Daily calorie target: {calories} kcal\n"
        f"BMI: {bmi} ({bmi_category})\n\n"
        "Hydration reminder: drink a glass of water now and try to stay consistent through the day.\n"
        "Meal reminder: check your personalized meal plan in NutriBot before your next meal.\n\n"
        "Regards,\nNutriBot"
    )
    return send_email(user["email"], "NutriBot Registration and Water Reminder", body)


def send_daily_meal_reminder():
    supabase = _get_supabase_client()
    groq_client = _get_groq_client()
    users = supabase.table("users").select("*").execute()
    for user in users.data:
        response = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{
                "role": "user",
                "content": f"Write a short friendly daily nutrition reminder for {user['name']} whose goal is {user['goal']} and daily calorie target is {user['daily_calories']} kcal. Keep it under 5 lines."
            }]
        )
        body = response.choices[0].message.content
        send_email(user['email'], "NutriBot Daily Reminder", body)


def send_water_reminder():
    supabase = _get_supabase_client()
    users = supabase.table("users").select("email, name").execute()
    for user in users.data:
        body = f"Hi {user['name']}! Reminder: Have you had enough water today? Aim for 8 glasses (2 liters) daily. Staying hydrated helps with metabolism and energy levels!"
        send_email(user['email'], "NutriBot Water Reminder", body)


def start_scheduler():
    if schedule is None:
        raise RuntimeError("Install the 'schedule' package to start notification scheduling.")

    schedule.every().day.at("08:00").do(send_daily_meal_reminder)
    schedule.every(2).hours.do(send_water_reminder)

    def run():
        while True:
            schedule.run_pending()
            time.sleep(60)

    t = threading.Thread(target=run, daemon=True)
    t.start()
    print("[NOTIFICATIONS] Scheduler started")
