import heapq


RECIPE_CATALOG = [
    {
        "name": "Greek Yogurt Berry Bowl",
        "meal_type": "breakfast",
        "ingredients": ["greek yogurt", "berries", "oats", "chia seeds"],
        "calories": 340,
        "protein": 28,
        "carbs": 42,
        "fat": 8,
        "nutrition_score": 88,
        "tags": ["vegetarian"],
    },
    {
        "name": "Veggie Omelette Toast",
        "meal_type": "breakfast",
        "ingredients": ["eggs", "spinach", "tomatoes", "whole wheat bread"],
        "calories": 390,
        "protein": 25,
        "carbs": 32,
        "fat": 17,
        "nutrition_score": 84,
        "tags": ["vegetarian"],
    },
    {
        "name": "Peanut Banana Oatmeal",
        "meal_type": "breakfast",
        "ingredients": ["oats", "banana", "peanut butter", "milk"],
        "calories": 430,
        "protein": 17,
        "carbs": 58,
        "fat": 16,
        "nutrition_score": 78,
        "tags": ["vegetarian"],
    },
    {
        "name": "Chicken Quinoa Bowl",
        "meal_type": "lunch",
        "ingredients": ["chicken", "quinoa", "cucumber", "tomatoes", "olive oil"],
        "calories": 560,
        "protein": 42,
        "carbs": 54,
        "fat": 18,
        "nutrition_score": 90,
        "tags": ["high protein"],
    },
    {
        "name": "Lentil Rice Plate",
        "meal_type": "lunch",
        "ingredients": ["lentils", "brown rice", "carrots", "onion", "yogurt"],
        "calories": 520,
        "protein": 24,
        "carbs": 78,
        "fat": 11,
        "nutrition_score": 86,
        "tags": ["vegetarian"],
    },
    {
        "name": "Tuna Chickpea Salad",
        "meal_type": "lunch",
        "ingredients": ["tuna", "chickpeas", "lettuce", "cucumber", "lemon"],
        "calories": 480,
        "protein": 39,
        "carbs": 44,
        "fat": 14,
        "nutrition_score": 87,
        "tags": ["high protein"],
    },
    {
        "name": "Turkey Avocado Wrap",
        "meal_type": "lunch",
        "ingredients": ["turkey", "avocado", "whole wheat tortilla", "lettuce"],
        "calories": 510,
        "protein": 35,
        "carbs": 45,
        "fat": 20,
        "nutrition_score": 82,
        "tags": ["high protein"],
    },
    {
        "name": "Salmon Sweet Potato Dinner",
        "meal_type": "dinner",
        "ingredients": ["salmon", "sweet potato", "broccoli", "olive oil"],
        "calories": 610,
        "protein": 43,
        "carbs": 52,
        "fat": 24,
        "nutrition_score": 92,
        "tags": ["high protein"],
    },
    {
        "name": "Paneer Vegetable Curry",
        "meal_type": "dinner",
        "ingredients": ["paneer", "spinach", "tomatoes", "brown rice"],
        "calories": 590,
        "protein": 30,
        "carbs": 58,
        "fat": 26,
        "nutrition_score": 80,
        "tags": ["vegetarian"],
    },
    {
        "name": "Chicken Stir Fry",
        "meal_type": "dinner",
        "ingredients": ["chicken", "bell peppers", "broccoli", "brown rice"],
        "calories": 570,
        "protein": 45,
        "carbs": 55,
        "fat": 16,
        "nutrition_score": 89,
        "tags": ["high protein"],
    },
    {
        "name": "Tofu Noodle Bowl",
        "meal_type": "dinner",
        "ingredients": ["tofu", "noodles", "carrots", "broccoli", "soy sauce"],
        "calories": 540,
        "protein": 28,
        "carbs": 68,
        "fat": 17,
        "nutrition_score": 81,
        "tags": ["vegetarian"],
    },
    {
        "name": "Apple Peanut Butter Snack",
        "meal_type": "snack",
        "ingredients": ["apple", "peanut butter"],
        "calories": 210,
        "protein": 7,
        "carbs": 28,
        "fat": 9,
        "nutrition_score": 76,
        "tags": ["vegetarian"],
    },
    {
        "name": "Boiled Eggs and Fruit",
        "meal_type": "snack",
        "ingredients": ["eggs", "orange"],
        "calories": 220,
        "protein": 14,
        "carbs": 20,
        "fat": 10,
        "nutrition_score": 79,
        "tags": ["vegetarian"],
    },
    {
        "name": "Cottage Cheese Cucumber Cup",
        "meal_type": "snack",
        "ingredients": ["cottage cheese", "cucumber", "black pepper"],
        "calories": 190,
        "protein": 22,
        "carbs": 11,
        "fat": 6,
        "nutrition_score": 83,
        "tags": ["vegetarian", "high protein"],
    },
    {
        "name": "Hummus Carrot Plate",
        "meal_type": "snack",
        "ingredients": ["hummus", "carrots", "whole wheat crackers"],
        "calories": 240,
        "protein": 9,
        "carbs": 34,
        "fat": 8,
        "nutrition_score": 77,
        "tags": ["vegetarian"],
    },
]


MEAL_SLOTS = ("breakfast", "lunch", "dinner", "snack")


def _normalize_words(values):
    return {str(item).strip().lower() for item in values if str(item).strip()}


def _matches_restrictions(recipe, restrictions):
    restriction_text = str(restrictions or "none").strip().lower()
    if not restriction_text or restriction_text == "none":
        return True

    tags = _normalize_words(recipe.get("tags", []))
    ingredients = _normalize_words(recipe.get("ingredients", []))

    if "vegetarian" in restriction_text and "vegetarian" not in tags:
        return False
    if "no fish" in restriction_text and {"salmon", "tuna"} & ingredients:
        return False
    if "nut" in restriction_text and {"peanut butter", "peanuts"} & ingredients:
        return False
    if "dairy" in restriction_text and {"milk", "yogurt", "greek yogurt", "paneer", "cottage cheese"} & ingredients:
        return False

    return True


def best_first_search(ingredients, recipes=None, limit=None):
    """
    Best-First Search ranks recipes by an overlap heuristic.
    The priority queue expands highest-scoring recipe matches first.
    """
    recipes = recipes or RECIPE_CATALOG
    normalized_ingredients = _normalize_words(ingredients)
    heap = []

    for index, recipe in enumerate(recipes):
        if not isinstance(recipe, dict):
            recipe = {"name": str(recipe), "ingredients": []}

        recipe_ingredients = _normalize_words(recipe.get("ingredients", []))
        matched = sorted(normalized_ingredients & recipe_ingredients)
        missing = sorted(recipe_ingredients - normalized_ingredients)
        overlap = len(matched)
        nutrition_score = int(recipe.get("nutrition_score", 50) or 0)
        score = (overlap * 20) + nutrition_score - (len(missing) * 2)

        payload = {
            **recipe,
            "matched_ingredients": matched,
            "missing_ingredients": missing,
            "search_score": score,
        }
        heapq.heappush(heap, (-score, -overlap, index, payload))

    results = []
    while heap and (limit is None or len(results) < limit):
        _, _, _, payload = heapq.heappop(heap)
        results.append(payload)

    return results


def build_backtracking_meal_plan(
    daily_calorie_target,
    restrictions=None,
    recipes=None,
    days=7,
    tolerance=250,
):
    """
    Backtracking Search builds a non-repetitive weekly plan.
    It fills each meal slot while keeping each day's calories near target.
    """
    recipes = [r for r in (recipes or RECIPE_CATALOG) if _matches_restrictions(r, restrictions)]
    by_slot = {
        slot: sorted(
            [r for r in recipes if r.get("meal_type") == slot],
            key=lambda r: r.get("nutrition_score", 0),
            reverse=True,
        )
        for slot in MEAL_SLOTS
    }

    if any(not by_slot[slot] for slot in MEAL_SLOTS):
        return {
            "success": False,
            "error": "Not enough recipes match the selected dietary restrictions.",
            "plan": [],
        }

    target = int(daily_calorie_target or 2000)
    used_counts = {}
    weekly_plan = []

    def max_uses_for(recipe):
        slot_count = max(len(by_slot[recipe["meal_type"]]), 1)
        return max(2, (days // slot_count) + 1)

    def recipe_penalty(recipe):
        return used_counts.get(recipe["name"], 0) * 100

    def search_day(day_index, slot_index, current_day, calories, best_match):
        if slot_index == len(MEAL_SLOTS):
            difference = abs(calories - target)
            score = difference + sum(recipe_penalty(recipe) for recipe in current_day)
            if best_match["score"] is None or score < best_match["score"]:
                best_match["score"] = score
                best_match["meals"] = list(current_day)
                best_match["calories"] = calories
            return abs(calories - target) <= tolerance

        slot = MEAL_SLOTS[slot_index]
        candidates = sorted(
            by_slot[slot],
            key=lambda r: (
                abs((calories + int(r["calories"])) - ((slot_index + 1) * target / len(MEAL_SLOTS))),
                recipe_penalty(r),
                -int(r.get("nutrition_score", 0)),
            ),
        )

        for recipe in candidates:
            if used_counts.get(recipe["name"], 0) >= max_uses_for(recipe):
                continue
            if current_day and current_day[-1]["name"] == recipe["name"]:
                continue

            used_counts[recipe["name"]] = used_counts.get(recipe["name"], 0) + 1
            current_day.append(recipe)

            if search_day(day_index, slot_index + 1, current_day, calories + int(recipe["calories"]), best_match):
                return True

            current_day.pop()
            used_counts[recipe["name"]] -= 1
            if used_counts[recipe["name"]] == 0:
                del used_counts[recipe["name"]]

        return False

    for day in range(1, days + 1):
        day_plan = []
        best_match = {"score": None, "meals": [], "calories": 0}
        if not search_day(day, 0, day_plan, 0, best_match):
            relaxed_tolerance = max(tolerance, 450)
            old_tolerance = tolerance
            tolerance = relaxed_tolerance
            found = search_day(day, 0, day_plan, 0, best_match)
            tolerance = old_tolerance
            if not found:
                day_plan = best_match["meals"]

        if not day_plan:
            return {
                "success": False,
                "error": f"Could not build day {day}; no meals were available for every slot.",
                "plan": weekly_plan,
            }

        total = sum(int(meal["calories"]) for meal in day_plan)
        weekly_plan.append({
            "day": day,
            "total_calories": total,
            "meals": day_plan,
        })

    return {
        "success": True,
        "algorithm": "Backtracking Search",
        "target_calories": target,
        "tolerance": tolerance,
        "plan": weekly_plan,
    }


def format_meal_plan(plan_result):
    if not plan_result.get("success"):
        return plan_result.get("error", "Meal plan could not be generated.")

    lines = [
        "Algorithm Used: Backtracking Search",
        f"Target: {plan_result['target_calories']} kcal/day",
        "",
    ]

    for day in plan_result["plan"]:
        lines.append(f"Day {day['day']} - Total: {day['total_calories']} kcal")
        for meal in day["meals"]:
            lines.append(
                f"- {meal['meal_type'].title()}: {meal['name']} "
                f"({meal['calories']} kcal, P {meal['protein']}g, "
                f"C {meal['carbs']}g, F {meal['fat']}g)"
            )
        lines.append("")

    return "\n".join(lines).strip()


def knapsack_grocery(items, calorie_budget):
    """
    Simple 0/1 knapsack using nutrition_score as value and calories as weight.
    Returns selected item names.
    """
    budget = max(int(calorie_budget), 0)
    normalized_items = []

    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        calories = int(item.get("calories", 0) or 0)
        score = int(item.get("nutrition_score", 0) or 0)
        if name and calories >= 0 and score >= 0:
            normalized_items.append((name, calories, score, item))

    dp = [[0] * (budget + 1) for _ in range(len(normalized_items) + 1)]

    for i, (_, calories, score, _) in enumerate(normalized_items, start=1):
        for capacity in range(budget + 1):
            dp[i][capacity] = dp[i - 1][capacity]
            if calories <= capacity:
                candidate = dp[i - 1][capacity - calories] + score
                if candidate > dp[i][capacity]:
                    dp[i][capacity] = candidate

    selected = []
    capacity = budget
    for i in range(len(normalized_items), 0, -1):
        if dp[i][capacity] != dp[i - 1][capacity]:
            name, calories, score, payload = normalized_items[i - 1]
            selected.append({
                **payload,
                "name": name,
                "calories": calories,
                "nutrition_score": score,
            })
            capacity -= calories

    selected.reverse()
    return {
        "algorithm": "0/1 Knapsack Dynamic Programming",
        "selected_items": selected,
        "total_calories": sum(item["calories"] for item in selected),
        "total_nutrition_score": sum(item["nutrition_score"] for item in selected),
    }
