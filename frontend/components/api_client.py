import os

import requests
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

def _get_base_url() -> str:
    """Resolve the backend URL from deployment config when available."""
    try:
        secret_url = st.secrets.get("BACKEND_URL")
    except StreamlitSecretNotFoundError:
        secret_url = None

    return (secret_url or os.getenv("BACKEND_URL") or "http://localhost:5000").rstrip("/")


BASE_URL = _get_base_url()


# ─── USER ────────────────────────────────────────────────────────────────────

def register_user(user_data: dict) -> dict:
    """
    POST /api/user/register
    Sends registration form data to Flask.
    Flask calculates BMI + calories and saves to Supabase.
    Returns the saved user dict or an error dict.
    """
    try:
        r = requests.post(f"{BASE_URL}/api/user/register", json=user_data)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def get_profile(email: str) -> dict:
    """
    GET /api/user/profile?email=...
    Fetches a user's full profile from Supabase via Flask.
    Returns user dict or {"error": "..."} if not found.
    """
    try:
        r = requests.get(f"{BASE_URL}/api/user/profile", params={"email": email})
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def update_profile(update_data: dict) -> dict:
    """
    PUT /api/user/update
    Sends updated fields (weight, goal, etc.) to Flask.
    Flask recalculates BMI + calories and saves updated values.
    """
    try:
        r = requests.put(f"{BASE_URL}/api/user/update", json=update_data)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


# ─── CHAT ────────────────────────────────────────────────────────────────────

def send_chat_message(email: str, message: str) -> dict:
    """
    POST /api/chat/message
    Sends one user message to Flask → Groq → saves both sides → returns reply.
    Returns {"reply": "..."} or {"error": "..."}.
    """
    try:
        r = requests.post(
            f"{BASE_URL}/api/chat/message",
            json={"email": email, "message": message}
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def get_chat_history(email: str) -> dict:
    """
    GET /api/chat/history?email=...
    Loads previous chat messages so the conversation
    is visible when the user reopens the app.
    """
    try:
        r = requests.get(f"{BASE_URL}/api/chat/history", params={"email": email})
        return r.json()
    except Exception as e:
        return {"error": str(e)}


# ─── MEAL PLAN ───────────────────────────────────────────────────────────────

def generate_meal_plan(email: str) -> dict:
    """
    POST /api/meal/generate
    Asks Flask to generate a 7-day meal plan with Backtracking Search.
    Returns {"meal_plan": "..."} with the full plan text.
    """
    try:
        r = requests.post(
            f"{BASE_URL}/api/meal/generate",
            json={"email": email}
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def get_latest_meal_plan(email: str) -> dict:
    """
    GET /api/meal/latest?email=...
    Fetches the most recently saved meal plan from Supabase.
    """
    try:
        r = requests.get(f"{BASE_URL}/api/meal/latest", params={"email": email})
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def suggest_from_ingredients(email: str, ingredients: list) -> dict:
    """
    POST /api/meal/ingredient-suggest
    Sends user's available ingredients to Flask.
    Returns {"suggestions": "..."} with 3 meal ideas.
    """
    try:
        r = requests.post(
            f"{BASE_URL}/api/meal/ingredient-suggest",
            json={"email": email, "ingredients": ingredients}
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def generate_grocery_list(email: str) -> dict:
    """
    POST /api/meal/grocery-list
    Asks Flask to generate a grocery list based on the latest meal plan.
    Returns {"grocery_list": "..."}.
    """
    try:
        r = requests.post(
            f"{BASE_URL}/api/meal/grocery-list",
            json={"email": email}
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def send_demo_notification(email: str) -> dict:
    """
    POST /api/user/send-demo-notification
    Sends one real email notification to the registered profile email.
    """
    try:
        r = requests.post(
            f"{BASE_URL}/api/user/send-demo-notification",
            json={"email": email},
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def optimize_grocery_items(items: list, calorie_budget: int) -> dict:
    """
    POST /api/meal/optimize-grocery
    Runs Knapsack DP to select the highest nutrition-score items within budget.
    """
    try:
        r = requests.post(
            f"{BASE_URL}/api/meal/optimize-grocery",
            json={"items": items, "calorie_budget": calorie_budget},
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def get_meal_health_score(calories: float, protein: float, carbs: float, fat: float) -> dict:
    """
    POST /api/meal/health-score
    Returns a lightweight health score for a meal.
    """
    try:
        r = requests.post(
            f"{BASE_URL}/api/meal/health-score",
            json={
                "calories": calories,
                "protein": protein,
                "carbs": carbs,
                "fat": fat,
            }
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def create_nutrition_log(email: str, food_description: str) -> dict:
    """
    POST /api/nutrition/log
    Estimates nutrition for a described meal and saves the entry.
    """
    try:
        r = requests.post(
            f"{BASE_URL}/api/nutrition/log",
            json={"email": email, "food_description": food_description}
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def get_nutrition_logs(email: str) -> dict:
    """
    GET /api/nutrition/logs?email=...
    Loads previously saved nutrition log entries.
    """
    try:
        r = requests.get(f"{BASE_URL}/api/nutrition/logs", params={"email": email})
        return r.json()
    except Exception as e:
        return {"error": str(e)}
