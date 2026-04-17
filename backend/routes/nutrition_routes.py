import re
from datetime import date

from flask import Blueprint, jsonify, request

from backend.services.groq_service import ask_groq_with_context
from backend.services.supabase_service import (
    get_logs_for_user,
    get_user_by_email,
    save_nutrition_log,
)

nutrition_bp = Blueprint("nutrition", __name__)


def _extract_number(pattern: str, text: str):
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return float(match.group(1)) if match else None


def _estimate_nutrition(food_description: str, user: dict):
    prompt = f"""
    Estimate the calories and macronutrients for this food:
    "{food_description}"

    Reply in this exact format:
    Calories: [number] kcal
    Protein: [number]g
    Carbohydrates: [number]g
    Fat: [number]g
    Brief note: [one sentence about this food]
    """
    reply = ask_groq_with_context(prompt, user)

    parsed = {
        "calories": _extract_number(r"Calories:\s*([0-9]+(?:\.[0-9]+)?)", reply),
        "protein_g": _extract_number(r"Protein:\s*([0-9]+(?:\.[0-9]+)?)", reply),
        "carbs_g": _extract_number(r"Carbohydrates:\s*([0-9]+(?:\.[0-9]+)?)", reply),
        "fat_g": _extract_number(r"Fat:\s*([0-9]+(?:\.[0-9]+)?)", reply),
    }
    return reply, parsed


@nutrition_bp.route("/log", methods=["POST"])
def create_nutrition_log():
    data = request.get_json()
    email = data.get("email")
    food_description = data.get("food_description")

    if not email or not food_description:
        return jsonify({"error": "email and food_description are required"}), 400

    user = get_user_by_email(email)
    if not user:
        return jsonify({"error": "User not found"}), 404

    reply, parsed = _estimate_nutrition(food_description, user)
    if any(value is None for value in parsed.values()):
        return jsonify({"error": "Failed to parse nutrition estimate", "reply": reply}), 502

    saved = save_nutrition_log({
        "user_id": user["id"],
        "date": str(date.today()),
        "food_description": food_description,
        "calories": int(round(parsed["calories"])),
        "protein_g": parsed["protein_g"],
        "carbs_g": parsed["carbs_g"],
        "fat_g": parsed["fat_g"],
    })

    return jsonify({"reply": reply, "log": saved}), 201


@nutrition_bp.route("/logs", methods=["GET"])
def list_nutrition_logs():
    email = request.args.get("email")
    if not email:
        return jsonify({"error": "email is required"}), 400

    user = get_user_by_email(email)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"logs": get_logs_for_user(user["id"])}), 200
