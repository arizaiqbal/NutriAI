import smtplib
import time
import threading
from datetime import datetime
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
        return (
            f"Hello {display_name}, wellness tip of the day: pair each meal with a glass of water "
            "and a short 5-minute walk for better energy and digestion."
        )
    return (
        "Wellness tip of the day: pair each meal with a glass of water "
        "and a short 5-minute walk for better energy and digestion."
    )


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
        return True, "Email notification sent successfully."
    except Exception as e:
        message = f"Email failed: {e}"
        print(f"[EMAIL] {message}", flush=True)
        return False, message


def send_demo_notification(user: dict):
    name = user.get("name", "there")
    goal = user.get("goal", "maintenance")
    calories = user.get("daily_calories", "your")
    body = (
        f"Dear {name},\n\n"
        "Welcome back to NutriBot.\n\n"
        "Here is your current profile summary:\n"
        f"- Goal: {goal}\n"
        f"- Daily calorie target: {calories} kcal\n\n"
        "Recommended actions for today:\n"
        "1. Follow your personalized meal plan for balanced intake.\n"
        "2. Maintain hydration throughout the day.\n"
        "3. Record your meals in the Nutrition Log for accurate tracking.\n\n"
        "Sincerely,\nNutriBot Support"
    )
    return send_email(user["email"], "NutriBot Login Nutrition Reminder", body)


def send_registration_notification(user: dict):
    name = user.get("name", "there")
    goal = user.get("goal", "maintenance")
    calories = user.get("daily_calories", "your")
    bmi = user.get("bmi", "N/A")
    bmi_category = user.get("bmi_category", "N/A")

    body = (
        f"Dear {name},\n\n"
        "Your NutriBot profile has been created successfully.\n\n"
        "Registered health summary:\n"
        f"- Goal: {goal}\n"
        f"- Daily calorie target: {calories} kcal\n"
        f"- BMI: {bmi} ({bmi_category})\n\n"
        "Next steps:\n"
        "1. Generate your 7-day meal plan.\n"
        "2. Review your grocery list generated from the plan.\n"
        "3. Log meals daily to track calorie and macronutrient intake.\n\n"
        "Sincerely,\nNutriBot Support"
    )
    return send_email(user["email"], "NutriBot Registration Confirmation", body)


def _goal_daily_suggestion(goal: str) -> str:
    normalized = str(goal or "maintenance").strip().lower()
    if normalized == "loss":
        return (
            "Prioritize high-fiber vegetables and lean protein in your next two meals, "
            "and avoid sugar-sweetened drinks for the rest of today."
        )
    if normalized == "gain":
        return (
            "Add one calorie-dense but balanced snack (for example yogurt with nuts or "
            "banana with peanut butter) to support healthy weight gain."
        )
    return (
        "Keep your meals balanced by including protein, complex carbohydrates, and "
        "vegetables in each main meal."
    )


def build_daily_nutrition_guidance(user: dict) -> str:
    name = user.get("name", "User")
    goal = user.get("goal", "maintenance")
    calories = user.get("daily_calories", "N/A")
    protein = user.get("protein_g", "N/A")
    carbs = user.get("carbs_g", "N/A")
    fat = user.get("fat_g", "N/A")
    today = datetime.now().strftime("%A")
    suggestion = _goal_daily_suggestion(goal)

    return (
        f"Dear {name},\n\n"
        f"This is your NutriBot daily nutrition guidance for {today}.\n\n"
        "Your current targets:\n"
        f"- Goal: {goal}\n"
        f"- Daily calories: {calories} kcal\n"
        f"- Protein target: {protein} g\n"
        f"- Carbohydrate target: {carbs} g\n"
        f"- Fat target: {fat} g\n\n"
        f"Today's suggestion:\n{suggestion}\n\n"
        "Please remember to stay hydrated and log your meals in NutriBot.\n\n"
        "Sincerely,\nNutriBot Support"
    )


def send_daily_meal_reminder():
    supabase = _get_supabase_client()
    users = supabase.table("users").select("*").execute()
    for user in users.data:
        body = build_daily_nutrition_guidance(user)
        send_email(user['email'], "NutriBot Daily Nutrition Guidance", body)


def send_water_reminder():
    supabase = _get_supabase_client()
    users = supabase.table("users").select("email, name").execute()
    for user in users.data:
        body = (
            f"Dear {user['name']},\n\n"
            "This is your hydration reminder from NutriBot.\n"
            "Please aim for regular water intake during the day (approximately 2 liters, unless advised otherwise by your clinician).\n\n"
            "Sincerely,\nNutriBot Support"
        )
        send_email(user['email'], "NutriBot Hydration Reminder", body)


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
