from supabase import create_client, Client
from backend.config import SUPABASE_URL, SUPABASE_KEY


def get_client() -> Client:
    """Creates and returns a Supabase client instance."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# ─── USER TABLE ──────────────────────────────────────────────────────────────

def save_user(user_data: dict) -> dict:
    """
    Inserts a new user profile into the 'users' table.
    
    Expected keys in user_data:
        email, name, height_cm, weight_kg, age, gender,
        goal, restrictions, daily_calories, bmi
    
    Returns the inserted row as a dict.
    """
    client = get_client()
    response = client.table("users").insert(user_data).execute()
    if response.data:
        return response.data[0]

    # Some Supabase/PostgREST setups return no inserted rows even when the
    # write succeeds, so re-fetch by email before treating this as a failure.
    return get_user_by_email(user_data["email"]) if user_data.get("email") else {}


def get_user_by_email(email: str) -> dict:
    """
    Fetches a user profile by email address.
    Returns the user dict, or empty dict if not found.
    """
    client = get_client()
    response = (
        client.table("users")
        .select("*")
        .eq("email", email)
        .execute()
    )
    return response.data[0] if response.data else {}


def update_user(email: str, updates: dict) -> dict:
    """
    Updates specific fields for a user identified by email.
    
    Example:
        update_user("a@b.com", {"weight_kg": 68, "bmi": 22.5})
    """
    client = get_client()
    response = (
        client.table("users")
        .update(updates)
        .eq("email", email)
        .execute()
    )
    return response.data[0] if response.data else {}


# ─── NUTRITION LOG TABLE ──────────────────────────────────────────────────────

def save_nutrition_log(log_data: dict) -> dict:
    """
    Saves a single nutrition log entry.
    
    Expected keys:
        user_id, date (YYYY-MM-DD), food_description,
        calories, protein_g, carbs_g, fat_g
    """
    client = get_client()
    response = client.table("nutrition_logs").insert(log_data).execute()
    return response.data[0] if response.data else {}


def get_logs_for_user(user_id: str, date: str = None) -> list:
    """
    Retrieves nutrition logs for a user.
    If date is provided (YYYY-MM-DD), filters to that day only.
    """
    client = get_client()
    query = client.table("nutrition_logs").select("*").eq("user_id", user_id)
    if date:
        query = query.eq("date", date)
    response = query.order("date", desc=True).execute()
    return response.data or []


# ─── MEAL PLAN TABLE ─────────────────────────────────────────────────────────

def save_meal_plan(plan_data: dict) -> dict:
    """
    Saves a weekly meal plan.
    
    Expected keys:
        user_id, week_start (YYYY-MM-DD), plan_json (stringified JSON)
    """
    client = get_client()
    response = client.table("meal_plans").insert(plan_data).execute()
    return response.data[0] if response.data else {}


def get_latest_meal_plan(user_id: str) -> dict:
    """
    Returns the most recently generated meal plan for a user.
    """
    client = get_client()
    response = (
        client.table("meal_plans")
        .select("*")
        .eq("user_id", user_id)
        .order("week_start", desc=True)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else {}


# ─── CHAT HISTORY TABLE ──────────────────────────────────────────────────────

def save_chat_message(user_id: str, role: str, message: str) -> dict:
    """
    Saves one chat message to history.
    
    Args:
        user_id: the user's UUID from Supabase
        role:    "user" or "assistant"
        message: the message text
    """
    client = get_client()
    response = client.table("chat_history").insert({
        "user_id": user_id,
        "role":    role,
        "message": message,
    }).execute()
    return response.data[0] if response.data else {}


def get_chat_history(user_id: str, limit: int = 20) -> list:
    """
    Returns the last `limit` messages for a user, oldest first
    (so they can be fed directly into the Groq messages list).
    """
    client = get_client()
    response = (
        client.table("chat_history")
        .select("role, message")
        .eq("user_id", user_id)
        .order("timestamp", desc=True)
        .limit(limit)
        .execute()
    )
    # reverse so oldest is first (chronological order for LLM context)
    return list(reversed(response.data or []))
