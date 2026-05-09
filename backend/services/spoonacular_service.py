import requests

from backend.config import SPOONACULAR_KEY


SPOONACULAR_BY_INGREDIENTS_URL = "https://api.spoonacular.com/recipes/findByIngredients"
SPOONACULAR_RECIPE_INFO_URL = "https://api.spoonacular.com/recipes/{recipe_id}/information"


def spoonacular_configured() -> bool:
    return bool(SPOONACULAR_KEY)


def find_recipes_by_ingredients(ingredients, limit=5):
    ingredient_text = ",".join(str(item).strip() for item in ingredients if str(item).strip())
    if not ingredient_text:
        return []

    response = requests.get(
        SPOONACULAR_BY_INGREDIENTS_URL,
        params={
            "apiKey": SPOONACULAR_KEY,
            "ingredients": ingredient_text,
            "number": limit,
            "ranking": 1,
            "ignorePantry": True,
        },
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def get_recipe_information(recipe_id: int):
    response = requests.get(
        SPOONACULAR_RECIPE_INFO_URL.format(recipe_id=recipe_id),
        params={"apiKey": SPOONACULAR_KEY, "includeNutrition": True},
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def build_ranked_recipe_suggestions(ingredients, limit=5):
    recipes = find_recipes_by_ingredients(ingredients, limit=limit)
    results = []
    for recipe in recipes:
        used = [item.get("name", "") for item in recipe.get("usedIngredients", [])]
        missed = [item.get("name", "") for item in recipe.get("missedIngredients", [])]
        overlap = len(used)
        missing = len(missed)
        score = (overlap * 20) - (missing * 3) + 50
        results.append(
            {
                "name": recipe.get("title", "Recipe"),
                "meal_type": "meal",
                "ingredients": used + missed,
                "matched_ingredients": used,
                "missing_ingredients": missed,
                "search_score": score,
                "nutrition_score": max(50, min(95, score)),
                "calories": 0,
                "protein": 0,
                "carbs": 0,
                "fat": 0,
                "source": "Spoonacular",
                "recipe_id": recipe.get("id"),
                "image": recipe.get("image"),
            }
        )
    return sorted(results, key=lambda row: row["search_score"], reverse=True)
