from flask import Blueprint, request, jsonify
from backend.services.groq_service import ask_groq_with_context
from backend.services.supabase_service import (
    get_user_by_email,
    save_meal_plan,
    get_latest_meal_plan
)
import json
from datetime import date

meal_bp = Blueprint("meal", __name__)


@meal_bp.route("/generate", methods=["POST"])
def generate_meal_plan():
    """
    Generates a 7-day personalized meal plan using Groq.
    In Phase 5 this will be upgraded to use Spoonacular + backtracking algorithm.
    For now it produces a well-structured text plan via LLM.

    Expects JSON body:
    {
        "email": "ariza@nu.edu.pk"
    }
    """
    data  = request.get_json()
    email = data.get("email")
    if not email:
        return jsonify({"error": "email is required"}), 400

    user = get_user_by_email(email)
    if not user:
        return jsonify({"error": "User not found"}), 404

    prompt = f"""
    Generate a 7-day meal plan for me. For each day include breakfast, lunch, dinner and one snack.
    For each meal provide:
    - Meal name
    - Approximate calories
    - Approximate protein, carbs, and fat in grams
    Keep total daily calories close to {user['daily_calories']} kcal.
    Dietary restrictions: {user.get('restrictions', 'none')}.
    Goal: {user['goal']}.
    Format each day clearly as Day 1, Day 2, etc.
    """

    plan_text = ask_groq_with_context(prompt, user)

    # save to Supabase
    save_meal_plan({
        "user_id":    user["id"],
        "week_start": str(date.today()),
        "plan_json":  json.dumps({"text": plan_text})
    })

    return jsonify({"meal_plan": plan_text}), 200


@meal_bp.route("/latest", methods=["GET"])
def get_latest_plan():
    """
    Returns the most recently saved meal plan for a user.
    Expects query parameter: ?email=ariza@nu.edu.pk
    """
    email = request.args.get("email")
    if not email:
        return jsonify({"error": "email is required"}), 400

    user = get_user_by_email(email)
    if not user:
        return jsonify({"error": "User not found"}), 404

    plan = get_latest_meal_plan(user["id"])
    if not plan:
        return jsonify({"message": "No meal plan found"}), 404

    plan_data = json.loads(plan["plan_json"])
    return jsonify({"meal_plan": plan_data.get("text", ""), "week_start": plan["week_start"]}), 200


@meal_bp.route("/ingredient-suggest", methods=["POST"])
def suggest_from_ingredients():
    """
    Takes a list of available ingredients and suggests meals.
    In Phase 5 this will use Best-First Search + Spoonacular.
    For now uses Groq directly.

    Expects JSON body:
    {
        "email":       "ariza@nu.edu.pk",
        "ingredients": ["chicken", "spinach", "garlic", "olive oil"]
    }
    """
    data        = request.get_json()
    email       = data.get("email")
    ingredients = data.get("ingredients", [])

    if not email or not ingredients:
        return jsonify({"error": "email and ingredients list are required"}), 400

    user = get_user_by_email(email)
    if not user:
        return jsonify({"error": "User not found"}), 404

    prompt = f"""
    I have these ingredients at home: {', '.join(ingredients)}.
    Suggest 3 healthy meals I can make using some or all of these.
    For each meal provide: name, ingredients used, estimated calories,
    estimated protein/carbs/fat, and brief preparation steps.
    Keep suggestions aligned with my goal: {user['goal']}.
    """

    suggestions = ask_groq_with_context(prompt, user)
    return jsonify({"suggestions": suggestions}), 200


@meal_bp.route("/grocery-list", methods=["POST"])
def generate_grocery_list():
    """
    Generates a grocery list based on the user's latest meal plan.
    In Phase 5 this will use Knapsack DP for optimization.
    For now uses Groq.

    Expects JSON body:
    {
        "email": "ariza@nu.edu.pk"
    }
    """
    data  = request.get_json()
    email = data.get("email")
    if not email:
        return jsonify({"error": "email is required"}), 400

    user = get_user_by_email(email)
    if not user:
        return jsonify({"error": "User not found"}), 404

    plan = get_latest_meal_plan(user["id"])
    if not plan:
        return jsonify({"error": "No meal plan found. Generate a meal plan first."}), 404

    plan_text = json.loads(plan["plan_json"]).get("text", "")

    prompt = f"""
    Based on this 7-day meal plan:
    {plan_text}
    
    Generate a complete grocery list organized by category:
    (Proteins, Vegetables, Fruits, Grains/Carbs, Dairy, Condiments/Spices)
    Include estimated quantities for one person for one week.
    """

    grocery_list = ask_groq_with_context(prompt, user)
    return jsonify({"grocery_list": grocery_list}), 200