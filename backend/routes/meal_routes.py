from flask import Blueprint, request, jsonify
from backend.services.ml_service import predict_calories, get_health_score, get_model_info
from backend.services.search_service import (
    RECIPE_CATALOG,
    best_first_search,
    build_backtracking_meal_plan,
    format_meal_plan,
    knapsack_grocery,
)
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
    Generates a 7-day personalized meal plan using Backtracking Search.
    Groq can still be used elsewhere for friendly explanations, but this
    endpoint keeps the compulsory AI algorithm visible in the main flow.

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

    plan_result = build_backtracking_meal_plan(
        daily_calorie_target=user.get("daily_calories", 2000),
        restrictions=user.get("restrictions", "none"),
    )
    if not plan_result.get("success"):
        return jsonify({"error": plan_result.get("error", "Failed to generate meal plan")}), 422

    plan_text = format_meal_plan(plan_result)

    # save to Supabase
    save_meal_plan({
        "user_id":    user["id"],
        "week_start": str(date.today()),
        "plan_json":  json.dumps({"text": plan_text, "algorithm_plan": plan_result})
    })

    return jsonify({
        "meal_plan": plan_text,
        "algorithm": plan_result["algorithm"],
        "plan": plan_result["plan"],
    }), 200


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
    Takes a list of available ingredients and suggests meals using
    Best-First Search over the recipe catalog.

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

    ranked = best_first_search(ingredients, RECIPE_CATALOG, limit=5)
    lines = ["Algorithm Used: Best-First Search", ""]
    for recipe in ranked[:3]:
        matched = ", ".join(recipe["matched_ingredients"]) or "none"
        missing = ", ".join(recipe["missing_ingredients"][:4]) or "none"
        lines.append(
            f"- {recipe['name']} ({recipe['meal_type'].title()}, score {recipe['search_score']}): "
            f"{recipe['calories']} kcal, P {recipe['protein']}g, C {recipe['carbs']}g, F {recipe['fat']}g. "
            f"Matched: {matched}. Missing: {missing}."
        )

    return jsonify({
        "algorithm": "Best-First Search",
        "suggestions": "\n".join(lines),
        "recipes": ranked,
    }), 200


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



@meal_bp.route("/ml-predict", methods=["POST"])
def ml_predict():
    data = request.json
    predicted = predict_calories(
        data["weight"], data["height"],
        data["age"], data["gender"],
        data.get("activity_level", 2)
    )
    return jsonify({
        "ml_predicted_calories": predicted,
        "model_info": get_model_info()
    })

@meal_bp.route("/health-score", methods=["POST"])
def health_score():
    data = request.json
    score = get_health_score(
        data.get("calories", 0),
        data.get("protein", 0),
        data.get("carbs", 0),
        data.get("fat", 0)
    )
    label = "Healthy" if score >= 70 else "Moderate" if score >= 50 else "Unhealthy"
    return jsonify({"health_score": score, "label": label})

@meal_bp.route("/search", methods=["POST"])
def search_recipes():
    data = request.json
    ingredients = data.get("ingredients", [])
    recipes = data.get("recipes", [])
    results = best_first_search(ingredients, recipes)
    return jsonify({"results": results})

@meal_bp.route("/optimize-grocery", methods=["POST"])
def optimize_grocery():
    data = request.json
    items = data.get("items", [])
    budget = data.get("calorie_budget", 2000)
    result = knapsack_grocery(items, budget)
    return jsonify({
        "algorithm": result["algorithm"],
        "optimized_list": result["selected_items"],
        "total_calories": result["total_calories"],
        "total_nutrition_score": result["total_nutrition_score"],
    })
