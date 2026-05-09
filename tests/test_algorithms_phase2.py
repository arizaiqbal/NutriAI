from backend.services.search_service import (
    build_backtracking_meal_plan,
    knapsack_grocery,
)


def test_backtracking_generates_seven_day_plan():
    result = build_backtracking_meal_plan(
        daily_calorie_target=2000,
        restrictions="none",
        days=7,
    )
    assert result["success"] is True
    assert result["algorithm"] == "Backtracking Search"
    assert len(result["plan"]) == 7
    for day in result["plan"]:
        assert len(day["meals"]) == 4
        assert day["total_calories"] > 0

    day_signatures = [
        tuple(meal["name"] for meal in day["meals"])
        for day in result["plan"]
    ]
    assert len(set(day_signatures)) == len(day_signatures)


def test_knapsack_respects_calorie_budget():
    items = [
        {"name": "Oats", "calories": 300, "nutrition_score": 80},
        {"name": "Eggs", "calories": 200, "nutrition_score": 85},
        {"name": "Apple", "calories": 100, "nutrition_score": 60},
        {"name": "Fries", "calories": 500, "nutrition_score": 20},
    ]
    result = knapsack_grocery(items, calorie_budget=600)
    assert result["algorithm"] == "0/1 Knapsack Dynamic Programming"
    assert result["total_calories"] <= 600
    assert result["total_nutrition_score"] >= 145
    assert [item["name"] for item in result["selected_items"]] == ["Oats", "Eggs", "Apple"]
