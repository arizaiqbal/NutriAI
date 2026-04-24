def best_first_search(ingredients, recipes):
    """
    Rank recipes by ingredient overlap so the API has a usable fallback.
    Each recipe can be a dict with `ingredients` or a plain string.
    """
    normalized_ingredients = {str(item).strip().lower() for item in ingredients if str(item).strip()}
    ranked = []

    for recipe in recipes:
        if isinstance(recipe, dict):
            recipe_ingredients = {
                str(item).strip().lower()
                for item in recipe.get("ingredients", [])
                if str(item).strip()
            }
            recipe_name = recipe.get("name", "Unnamed recipe")
            payload = recipe
        else:
            recipe_name = str(recipe)
            recipe_ingredients = set()
            payload = {"name": recipe_name, "ingredients": []}

        overlap = len(normalized_ingredients & recipe_ingredients)
        missing = len(recipe_ingredients - normalized_ingredients)
        score = overlap * 10 - missing
        ranked.append((score, overlap, payload))

    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [item[2] for item in ranked]


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
            normalized_items.append((name, calories, score))

    dp = [[0] * (budget + 1) for _ in range(len(normalized_items) + 1)]

    for i, (_, calories, score) in enumerate(normalized_items, start=1):
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
            name, calories, _ = normalized_items[i - 1]
            selected.append(name)
            capacity -= calories

    selected.reverse()
    return selected
