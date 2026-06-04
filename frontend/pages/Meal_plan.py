import os
import sys

import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from frontend.components.api_client import (
    generate_grocery_list,
    generate_meal_plan,
    get_latest_meal_plan,
    optimize_grocery_items,
    suggest_from_ingredients,
)
from frontend.components.ui_helpers import apply_theme, require_login, show_card, show_error, show_feature_grid, show_macro_charts, show_success


st.set_page_config(page_title="Meal Plan - NutriAI", page_icon="🍽️")

apply_theme(
    "Meal Planning",
    "Design a softer weekly flow with meal plans, ingredient-based ideas, and a matching grocery helper.",
    badge="Meal Planning",
)

user = require_login()
if not user:
    st.stop()

show_feature_grid([
    ("Daily target", f"{user.get('daily_calories', 0)} kcal"),
    ("Goal", user.get("goal", "").capitalize()),
    ("Restrictions", user.get("restrictions", "none").capitalize()),
])
show_macro_charts(
    user.get("protein_g", 0),
    user.get("carbs_g", 0),
    user.get("fat_g", 0),
    title="Plan Macro Targets",
    subtitle="Use this target mix as the visual guide for your weekly meal plan.",
)

tab_plan, tab_ingredients, tab_grocery = st.tabs([
    "7-Day Meal Plan",
    "Ingredient-Based Suggestions",
    "Grocery List",
])

with tab_plan:
    show_card("7-day plan", f"Generate a personalized plan built around {user.get('daily_calories')} kcal per day.")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Generate New Meal Plan", use_container_width=True):
            with st.spinner("Building your 7-day plan..."):
                result = generate_meal_plan(user["email"])

            if "error" in result:
                show_error(result["error"])
            else:
                st.session_state["meal_plan"] = result["meal_plan"]
                show_success("Meal plan generated and saved!")

    with col2:
        if st.button("Load Saved Plan", use_container_width=True):
            with st.spinner("Loading your latest plan..."):
                result = get_latest_meal_plan(user["email"])

            if "error" in result:
                show_error(result.get("error", "No saved plan found."))
            else:
                st.session_state["meal_plan"] = result.get("meal_plan", "")
                if result.get("week_start"):
                    st.caption(f"Plan from: {result['week_start']}")

    if st.session_state.get("meal_plan"):
        st.markdown("### Your 7-Day Plan")
        show_card("Fresh plan", st.session_state["meal_plan"])

with tab_ingredients:
    show_card("Ingredient ideas", "Tell NutriAI what is in your kitchen to get ranked meal suggestions based on ingredient overlap and nutrition quality.")
    ingredient_input = st.text_area(
        "Available Ingredients",
        placeholder="chicken, spinach, garlic, olive oil, tomatoes, onion",
        height=100,
    )

    if st.button("Find Meals", use_container_width=True):
        if not ingredient_input.strip():
            show_error("Please enter at least one ingredient.")
        else:
            ingredients = [i.strip() for i in ingredient_input.split(",") if i.strip()]
            with st.spinner(f"Searching for meals using {len(ingredients)} ingredients..."):
                result = suggest_from_ingredients(user["email"], ingredients)

            if "error" in result:
                show_error(result["error"])
            else:
                show_card("Suggested meals", result["suggestions"])

with tab_grocery:
    show_card("Grocery helper", "Turn your latest meal plan into a shopping list, or optimize food choices inside a calorie budget.")
    if not st.session_state.get("meal_plan"):
        st.info("Generate or load a meal plan first, then come back here.")

    if st.button("Generate Grocery List", use_container_width=True):
        with st.spinner("Building your grocery list..."):
            result = generate_grocery_list(user["email"])

        if "error" in result:
            show_error(result["error"])
        else:
            show_card("Your grocery list", result["grocery_list"])

    st.divider()
    st.markdown("### Grocery Optimizer")
    calorie_budget = st.number_input("Calorie budget", 500, 4000, int(user.get("daily_calories", 2000)))
    item_count = st.number_input("Number of candidate items", 1, 12, 4)

    optimizer_items = []
    for i in range(item_count):
        col1, col2, col3 = st.columns(3)
        with col1:
            name = st.text_input(f"Food item {i + 1}", key=f"meal_opt_name_{i}")
        with col2:
            calories = st.number_input("Calories", 0, 1200, 250, key=f"meal_opt_cal_{i}")
        with col3:
            score = st.number_input("Nutrition score", 1, 100, 70, key=f"meal_opt_score_{i}")
        if name.strip():
            optimizer_items.append({
                "name": name.strip(),
                "calories": calories,
                "nutrition_score": score,
            })

    if st.button("Optimize Grocery Picks", use_container_width=True):
        if not optimizer_items:
            show_error("Please add at least one food item.")
        else:
            result = optimize_grocery_items(optimizer_items, calorie_budget)
            if "error" in result:
                show_error(result["error"])
            else:
                selected = result.get("optimized_list", [])
                lines = [
                    f"Total calories: {result.get('total_calories', 0)}",
                    f"Total nutrition score: {result.get('total_nutrition_score', 0)}",
                    "",
                ]
                lines.extend(
                    f"- {item['name']} ({item['calories']} kcal, score {item['nutrition_score']})"
                    for item in selected
                )
                show_card("Optimized grocery picks", "<br>".join(lines))
