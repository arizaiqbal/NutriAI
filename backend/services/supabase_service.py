import json
import uuid
from datetime import datetime
from pathlib import Path

from supabase import create_client, Client
from backend.config import SUPABASE_URL, SUPABASE_KEY


LOCAL_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "local_db.json"
TABLE_DEFAULTS = {
    "users": [],
    "nutrition_logs": [],
    "meal_plans": [],
    "chat_history": [],
}


def _load_local_db() -> dict:
    if not LOCAL_DB_PATH.exists():
        return {table: rows.copy() for table, rows in TABLE_DEFAULTS.items()}

    try:
        with LOCAL_DB_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        data = {}

    for table, rows in TABLE_DEFAULTS.items():
        data.setdefault(table, rows.copy())
    return data


def _save_local_db(data: dict) -> None:
    LOCAL_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOCAL_DB_PATH.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def _new_id() -> str:
    return str(uuid.uuid4())


def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def _local_save_user(user_data: dict) -> dict:
    db = _load_local_db()
    existing = next((row for row in db["users"] if row.get("email") == user_data.get("email")), None)
    if existing:
        existing.update(user_data)
        existing.setdefault("id", _new_id())
        saved = existing
    else:
        saved = {"id": _new_id(), **user_data}
        db["users"].append(saved)
    _save_local_db(db)
    return saved


def _local_get_user_by_email(email: str) -> dict:
    db = _load_local_db()
    return next((row for row in db["users"] if row.get("email") == email), {})


def _local_update_user(email: str, updates: dict) -> dict:
    db = _load_local_db()
    for row in db["users"]:
        if row.get("email") == email:
            row.update(updates)
            _save_local_db(db)
            return row
    return {}


def _local_insert(table: str, data: dict) -> dict:
    db = _load_local_db()
    row = {"id": _new_id(), **data}
    if table == "chat_history":
        row.setdefault("timestamp", _now_iso())
    db[table].append(row)
    _save_local_db(db)
    return row


def _local_rows_for_user(table: str, user_id: str) -> list:
    db = _load_local_db()
    return [row for row in db[table] if row.get("user_id") == user_id]


def _supabase_or_local(operation, fallback):
    try:
        return operation()
    except Exception as exc:
        print(f"[LOCAL FALLBACK] Supabase unavailable: {exc}")
        return fallback()


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
    def operation():
        client = get_client()
        response = client.table("users").insert(user_data).execute()
        if response.data:
            return response.data[0]
        return get_user_by_email(user_data["email"]) if user_data.get("email") else {}

    return _supabase_or_local(operation, lambda: _local_save_user(user_data))


def get_user_by_email(email: str) -> dict:
    """
    Fetches a user profile by email address.
    Returns the user dict, or empty dict if not found.
    """
    def operation():
        client = get_client()
        response = (
            client.table("users")
            .select("*")
            .eq("email", email)
            .execute()
        )
        return response.data[0] if response.data else {}

    return _supabase_or_local(operation, lambda: _local_get_user_by_email(email))


def update_user(email: str, updates: dict) -> dict:
    """
    Updates specific fields for a user identified by email.
    
    Example:
        update_user("a@b.com", {"weight_kg": 68, "bmi": 22.5})
    """
    def operation():
        client = get_client()
        response = (
            client.table("users")
            .update(updates)
            .eq("email", email)
            .execute()
        )
        return response.data[0] if response.data else {}

    return _supabase_or_local(operation, lambda: _local_update_user(email, updates))


# ─── NUTRITION LOG TABLE ──────────────────────────────────────────────────────

def save_nutrition_log(log_data: dict) -> dict:
    """
    Saves a single nutrition log entry.
    
    Expected keys:
        user_id, date (YYYY-MM-DD), food_description,
        calories, protein_g, carbs_g, fat_g
    """
    return _supabase_or_local(
        lambda: get_client().table("nutrition_logs").insert(log_data).execute().data[0],
        lambda: _local_insert("nutrition_logs", log_data),
    )


def get_logs_for_user(user_id: str, date: str = None) -> list:
    """
    Retrieves nutrition logs for a user.
    If date is provided (YYYY-MM-DD), filters to that day only.
    """
    def operation():
        client = get_client()
        query = client.table("nutrition_logs").select("*").eq("user_id", user_id)
        if date:
            query = query.eq("date", date)
        response = query.order("date", desc=True).execute()
        return response.data or []

    def fallback():
        rows = _local_rows_for_user("nutrition_logs", user_id)
        if date:
            rows = [row for row in rows if row.get("date") == date]
        return sorted(rows, key=lambda row: row.get("date", ""), reverse=True)

    return _supabase_or_local(operation, fallback)


# ─── MEAL PLAN TABLE ─────────────────────────────────────────────────────────

def save_meal_plan(plan_data: dict) -> dict:
    """
    Saves a weekly meal plan.
    
    Expected keys:
        user_id, week_start (YYYY-MM-DD), plan_json (stringified JSON)
    """
    return _supabase_or_local(
        lambda: get_client().table("meal_plans").insert(plan_data).execute().data[0],
        lambda: _local_insert("meal_plans", plan_data),
    )


def get_latest_meal_plan(user_id: str) -> dict:
    """
    Returns the most recently generated meal plan for a user.
    """
    def operation():
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

    def fallback():
        rows = _local_rows_for_user("meal_plans", user_id)
        rows = sorted(rows, key=lambda row: row.get("week_start", ""), reverse=True)
        return rows[0] if rows else {}

    return _supabase_or_local(operation, fallback)


# ─── CHAT HISTORY TABLE ──────────────────────────────────────────────────────

def save_chat_message(user_id: str, role: str, message: str) -> dict:
    """
    Saves one chat message to history.
    
    Args:
        user_id: the user's UUID from Supabase
        role:    "user" or "assistant"
        message: the message text
    """
    row = {
        "user_id": user_id,
        "role":    role,
        "message": message,
    }

    return _supabase_or_local(
        lambda: get_client().table("chat_history").insert(row).execute().data[0],
        lambda: _local_insert("chat_history", row),
    )


def get_chat_history(user_id: str, limit: int = 20) -> list:
    """
    Returns the last `limit` messages for a user, oldest first
    (so they can be fed directly into the Groq messages list).
    """
    def operation():
        client = get_client()
        response = (
            client.table("chat_history")
            .select("role, message")
            .eq("user_id", user_id)
            .order("timestamp", desc=True)
            .limit(limit)
            .execute()
        )
        return list(reversed(response.data or []))

    def fallback():
        rows = _local_rows_for_user("chat_history", user_id)
        rows = sorted(rows, key=lambda row: row.get("timestamp", ""))
        return [{"role": row.get("role"), "message": row.get("message")} for row in rows[-limit:]]

    return _supabase_or_local(operation, fallback)
