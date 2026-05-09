import re
import json
from datetime import date

from flask import Blueprint, jsonify, request

from backend.services.groq_service import ask_groq_with_context
from backend.services.usda_service import estimate_items, usda_configured
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


def _extract_json_array(text: str):
    content = text.strip()
    if content.startswith("```"):
        content = re.sub(r"^```[a-zA-Z]*\n", "", content)
        content = re.sub(r"\n```$", "", content)
    start = content.find("[")
    end = content.rfind("]")
    if start == -1 or end == -1 or end < start:
        return []
    try:
        return json.loads(content[start : end + 1])
    except json.JSONDecodeError:
        return []


def _parse_food_items_with_groq(food_description: str, user: dict):
    prompt = f"""
    Convert this meal description into a JSON array.
    Input: "{food_description}"

    Rules:
    - Return ONLY JSON, no markdown.
    - Each item must be: {{"food":"...", "quantity": number, "unit":"..."}}
    - Keep quantity numeric.
    - If quantity is missing, use 1.
    - If unit is missing, use "serving".
    """
    reply = ask_groq_with_context(prompt, user)
    items = _extract_json_array(reply)
    normalized = []
    for item in items:
        if not isinstance(item, dict):
            continue
        food = str(item.get("food", "")).strip()
        if not food:
            continue
        try:
            quantity = float(item.get("quantity", 1) or 1)
        except (TypeError, ValueError):
            quantity = 1.0
        unit = str(item.get("unit", "serving")).strip() or "serving"
        normalized.append({"food": food, "quantity": quantity, "unit": unit})
    return normalized


def _estimate_with_usda(food_description: str, user: dict):
    items = _parse_food_items_with_groq(food_description, user)
    if not items:
        return None

    totals, breakdown = estimate_items(items)
    if not breakdown:
        return None

    reply_lines = ["USDA-based estimate:", ""]
    for row in breakdown:
        reply_lines.append(
            f"- {row['food']} ({row['quantity']} {row['unit']}): "
            f"{row['calories']} kcal, P {row['protein_g']}g, C {row['carbs_g']}g, F {row['fat_g']}g"
        )
    reply_lines.extend(
        [
            "",
            f"Calories: {round(totals['calories'], 1)} kcal",
            f"Protein: {round(totals['protein_g'], 1)}g",
            f"Carbohydrates: {round(totals['carbs_g'], 1)}g",
            f"Fat: {round(totals['fat_g'], 1)}g",
            "Brief note: Estimated via USDA FoodData search + quantity conversion.",
        ]
    )
    return {
        "reply": "\n".join(reply_lines),
        "parsed": {
            "calories": totals["calories"],
            "protein_g": totals["protein_g"],
            "carbs_g": totals["carbs_g"],
            "fat_g": totals["fat_g"],
        },
        "source": "USDA",
    }


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

    estimate = _estimate_with_usda(food_description, user) if usda_configured() else None
    source = "LLM"
    if estimate:
        reply = estimate["reply"]
        parsed = estimate["parsed"]
        source = estimate["source"]
    else:
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

    return jsonify({"reply": reply, "log": saved, "source": source}), 201


@nutrition_bp.route("/logs", methods=["GET"])
def list_nutrition_logs():
    email = request.args.get("email")
    if not email:
        return jsonify({"error": "email is required"}), 400

    user = get_user_by_email(email)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"logs": get_logs_for_user(user["id"])}), 200
