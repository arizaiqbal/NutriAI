from flask import Blueprint, request, jsonify
from backend.services.ml_service import predict_calories, get_health_score, get_model_info
from backend.services.search_service import (
    RECIPE_CATALOG,
    best_first_search,
    build_backtracking_meal_plan,
    format_meal_plan,
    knapsack_grocery,
)
from backend.services.spoonacular_service import (
    build_ranked_recipe_suggestions,
    spoonacular_configured,
)
from backend.services.supabase_service import (
    get_user_by_email,
    save_meal_plan,
    get_latest_meal_plan
)
import json
from datetime import date
from collections import Counter

meal_bp = Blueprint("meal", __name__)

INGREDIENT_PROFILES = {
    "chicken": {"category": "Proteins", "calories": 165, "nutrition_score": 88},
    "eggs": {"category": "Proteins", "calories": 155, "nutrition_score": 84},
    "tuna": {"category": "Proteins", "calories": 132, "nutrition_score": 85},
    "salmon": {"category": "Proteins", "calories": 208, "nutrition_score": 92},
    "tofu": {"category": "Proteins", "calories": 76, "nutrition_score": 82},
    "paneer": {"category": "Proteins", "calories": 265, "nutrition_score": 76},
    "lentils": {"category": "Grains/Carbs", "calories": 116, "nutrition_score": 86},
    "chickpeas": {"category": "Grains/Carbs", "calories": 164, "nutrition_score": 84},
    "quinoa": {"category": "Grains/Carbs", "calories": 120, "nutrition_score": 87},
    "brown rice": {"category": "Grains/Carbs", "calories": 111, "nutrition_score": 80},
    "oats": {"category": "Grains/Carbs", "calories": 389, "nutrition_score": 83},
    "sweet potato": {"category": "Vegetables", "calories": 86, "nutrition_score": 85},
    "broccoli": {"category": "Vegetables", "calories": 34, "nutrition_score": 89},
    "spinach": {"category": "Vegetables", "calories": 23, "nutrition_score": 90},
    "carrots": {"category": "Vegetables", "calories": 41, "nutrition_score": 84},
    "cucumber": {"category": "Vegetables", "calories": 16, "nutrition_score": 80},
    "tomatoes": {"category": "Vegetables", "calories": 18, "nutrition_score": 82},
    "apple": {"category": "Fruits", "calories": 52, "nutrition_score": 80},
    "banana": {"category": "Fruits", "calories": 89, "nutrition_score": 78},
    "berries": {"category": "Fruits", "calories": 57, "nutrition_score": 88},
    "orange": {"category": "Fruits", "calories": 47, "nutrition_score": 79},
    "greek yogurt": {"category": "Dairy", "calories": 59, "nutrition_score": 82},
    "milk": {"category": "Dairy", "calories": 61, "nutrition_score": 75},
    "cottage cheese": {"category": "Dairy", "calories": 98, "nutrition_score": 84},
    "olive oil": {"category": "Condiments/Spices", "calories": 119, "nutrition_score": 68},
    "peanut butter": {"category": "Condiments/Spices", "calories": 588, "nutrition_score": 65},
}


def _build_grocery_candidates_from_plan(plan_json: dict):
    algorithm_plan = plan_json.get("algorithm_plan", {})
    weekly_days = algorithm_plan.get("plan", [])
    ingredient_counts = Counter()

    for day in weekly_days:
        for meal in day.get("meals", []):
            for ingredient in meal.get("ingredients", []):
                ingredient_counts[str(ingredient).strip().lower()] += 1

    candidates = []
    for ingredient, count in ingredient_counts.items():
        profile = INGREDIENT_PROFILES.get(
            ingredient,
            {"category": "Other", "calories": 90, "nutrition_score": 60},
        )
        candidates.append(
            {
                "name": ingredient.title(),
                "category": profile["category"],
                "quantity_estimate": f"{count} unit(s)",
                "calories": int(profile["calories"]),
                "nutrition_score": int(profile["nutrition_score"]),
            }
        )
    return candidates


def _format_grouped_grocery_list(candidates, optimized):
    grouped = {}
    for item in candidates:
        grouped.setdefault(item["category"], []).append(item)

    lines = ["Complete ingredients from your weekly meal plan:"]
    for category in ["Proteins", "Vegetables", "Fruits", "Grains/Carbs", "Dairy", "Condiments/Spices", "Other"]:
        items = grouped.get(category, [])
        if not items:
            continue
        lines.append(f"- {category}:")
        for item in sorted(items, key=lambda row: row["name"]):
            lines.append(f"  - {item['name']} ({item['quantity_estimate']})")

    lines.extend(["", "Priority picks for your calorie target:"])
    for item in optimized:
        lines.append(
            f"- {item['name']} ({item['calories']} kcal, nutrition score {item['nutrition_score']})"
        )
    return "\n".join(lines)


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

    source = "Local Catalog"
    algorithm = "Best-First Search"
    ranked = []
    if spoonacular_configured():
        try:
            ranked = build_ranked_recipe_suggestions(ingredients, limit=5)
            source = "Spoonacular API"
        except Exception:
            ranked = []

    if not ranked:
        ranked = best_first_search(ingredients, RECIPE_CATALOG, limit=5)

    lines = [f"Data Source: {source}", ""]
    for recipe in ranked[:3]:
        matched = ", ".join(recipe["matched_ingredients"]) or "none"
        missing = ", ".join(recipe["missing_ingredients"][:4]) or "none"
        lines.append(
            f"- {recipe['name']} ({recipe['meal_type'].title()}, score {recipe['search_score']}): "
            f"{recipe['calories']} kcal, P {recipe['protein']}g, C {recipe['carbs']}g, F {recipe['fat']}g. "
            f"Matched: {matched}. Missing: {missing}."
        )

    return jsonify({
        "algorithm": algorithm,
        "source": source,
        "suggestions": "\n".join(lines),
        "recipes": ranked,
    }), 200


@meal_bp.route("/grocery-list", methods=["POST"])
def generate_grocery_list():
    """
    Generates a grocery list based on the user's latest meal plan.
    Uses Knapsack DP to optimize priority items under calorie budget.

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

    plan_json = json.loads(plan["plan_json"])
    candidates = _build_grocery_candidates_from_plan(plan_json)
    if not candidates:
        return jsonify({"error": "Could not extract ingredients from meal plan."}), 422

    calorie_budget = int(user.get("daily_calories", 2000))
    optimized = knapsack_grocery(candidates, calorie_budget)
    grocery_text = _format_grouped_grocery_list(candidates, optimized["selected_items"])

    return jsonify(
        {
            "algorithm": optimized["algorithm"],
            "calorie_budget": calorie_budget,
            "total_calories": optimized["total_calories"],
            "total_nutrition_score": optimized["total_nutrition_score"],
            "optimized_items": optimized["selected_items"],
            "all_items": candidates,
            "grocery_list": grocery_text,
        }
    ), 200



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
