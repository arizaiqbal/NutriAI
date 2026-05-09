import re
from typing import Dict, List, Tuple

import requests

from backend.config import USDA_KEY


USDA_SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

_GRAM_CONVERSIONS = {
    "g": 1.0,
    "gram": 1.0,
    "grams": 1.0,
    "kg": 1000.0,
    "oz": 28.35,
    "ounce": 28.35,
    "ounces": 28.35,
    "lb": 453.6,
    "pound": 453.6,
    "pounds": 453.6,
    "ml": 1.0,
    "l": 1000.0,
    "cup": 240.0,
    "cups": 240.0,
    "tbsp": 15.0,
    "tablespoon": 15.0,
    "tablespoons": 15.0,
    "tsp": 5.0,
    "teaspoon": 5.0,
    "teaspoons": 5.0,
    "piece": 100.0,
    "pieces": 100.0,
    "serving": 100.0,
    "servings": 100.0,
}


def usda_configured() -> bool:
    return bool(USDA_KEY)


def _normalize_unit(unit: str) -> str:
    return re.sub(r"[^a-z]", "", str(unit or "").strip().lower())


def _to_grams(quantity: float, unit: str) -> float:
    normalized = _normalize_unit(unit)
    multiplier = _GRAM_CONVERSIONS.get(normalized, 100.0)
    return max(0.0, float(quantity or 0)) * multiplier


def _extract_nutrients(food: dict) -> Dict[str, float]:
    calories = protein = carbs = fat = 0.0
    for nutrient in food.get("foodNutrients", []):
        name = str(nutrient.get("nutrientName", "")).strip().lower()
        value = float(nutrient.get("value") or 0.0)
        if "energy" in name and "kcal" in name:
            calories = value
        elif "protein" in name:
            protein = value
        elif "carbohydrate" in name:
            carbs = value
        elif name == "total lipid (fat)" or "fat" == name:
            fat = value
    return {
        "calories_per_100g": calories,
        "protein_per_100g": protein,
        "carbs_per_100g": carbs,
        "fat_per_100g": fat,
    }


def search_food(food_name: str) -> dict:
    response = requests.get(
        USDA_SEARCH_URL,
        params={"api_key": USDA_KEY, "query": food_name, "pageSize": 1},
        timeout=15,
    )
    response.raise_for_status()
    foods = response.json().get("foods", [])
    return foods[0] if foods else {}


def estimate_items(items: List[dict]) -> Tuple[dict, List[dict]]:
    totals = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}
    breakdown: List[dict] = []

    for item in items:
        name = str(item.get("food", "")).strip()
        if not name:
            continue

        quantity = float(item.get("quantity", 1) or 1)
        unit = str(item.get("unit", "serving"))
        grams = _to_grams(quantity, unit)

        food = search_food(name)
        if not food:
            continue

        nutrients = _extract_nutrients(food)
        factor = grams / 100.0
        calories = nutrients["calories_per_100g"] * factor
        protein = nutrients["protein_per_100g"] * factor
        carbs = nutrients["carbs_per_100g"] * factor
        fat = nutrients["fat_per_100g"] * factor

        totals["calories"] += calories
        totals["protein_g"] += protein
        totals["carbs_g"] += carbs
        totals["fat_g"] += fat

        breakdown.append(
            {
                "food": name,
                "quantity": quantity,
                "unit": unit,
                "grams_estimate": round(grams, 1),
                "fdc_description": food.get("description", ""),
                "calories": round(calories, 1),
                "protein_g": round(protein, 1),
                "carbs_g": round(carbs, 1),
                "fat_g": round(fat, 1),
            }
        )

    return totals, breakdown
