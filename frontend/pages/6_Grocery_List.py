import os
import sys

import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from frontend.components.api_client import (
    generate_grocery_list,
    get_latest_meal_plan,
    optimize_grocery_items,
)
from frontend.components.ui_helpers import apply_theme, require_login, show_card, show_error, show_success


st.set_page_config(page_title="Grocery List - NutriAI", page_icon="🛒")

apply_theme(
    "Grocery List",
    "Generate a shopping list from a meal plan or optimize item choices with a colorful little planner.",
    badge="Grocery Planning",
)

show_card("Generate from saved meal plan", "Load your latest saved meal plan and generate a grocery list automatically, or use the optimizer below to choose the best items inside a calorie budget.")
user = require_login()
if not user:
    st.stop()

if "grocery_page_meal_plan" not in st.session_state:
    st.session_state["grocery_page_meal_plan"] = ""

if "grocery_page_list" not in st.session_state:
    st.session_state["grocery_page_list"] = ""

col1, col2 = st.columns(2)
with col1:
    if st.button("Load Latest Meal Plan", use_container_width=True):
        with st.spinner("Loading your latest meal plan..."):
            result = get_latest_meal_plan(user["email"])
        if "error" in result:
            show_error(result.get("error", "No saved meal plan found."))
        else:
            st.session_state["grocery_page_meal_plan"] = result.get("meal_plan", "")
            show_success("Latest meal plan loaded.")

with col2:
    if st.button("Generate Grocery List Automatically", use_container_width=True):
        with st.spinner("Generating grocery list from your latest saved meal plan..."):
            result = generate_grocery_list(user["email"])
        if "error" in result:
            show_error(result["error"])
        else:
            st.session_state["grocery_page_list"] = result.get("grocery_list", "")
            show_success("Grocery list generated automatically.")

if st.session_state["grocery_page_meal_plan"]:
    show_card("Latest saved meal plan", st.session_state["grocery_page_meal_plan"])

if st.session_state["grocery_page_list"]:
    show_card("Your grocery list", st.session_state["grocery_page_list"])

st.divider()
show_card("Optimize Grocery List", "Enter candidate items and Knapsack DP will pick the highest nutrition-score set within your calorie budget.")

calorie_budget = st.number_input("Daily calorie budget", 1000, 4000, 2000)

items = []
num_items = st.number_input("How many items?", 1, 20, 5)
for i in range(num_items):
    col1, col2, col3 = st.columns(3)
    with col1:
        name = st.text_input(f"Item {i + 1} name", key=f"name_{i}")
    with col2:
        cal = st.number_input("Calories", 0, 1000, 100, key=f"cal_{i}")
    with col3:
        score = st.number_input("Nutrition score (1-10)", 1, 10, 5, key=f"score_{i}")
    if name:
        items.append({"name": name, "calories": cal, "nutrition_score": score})

if st.button("Optimize List", use_container_width=True):
    if items:
        data = optimize_grocery_items(items, calorie_budget)
        if "error" not in data:
            selected = data.get("optimized_list", [])
            lines = [
                f"Total calories: {data.get('total_calories', 0)}",
                f"Total nutrition score: {data.get('total_nutrition_score', 0)}",
                "",
            ]
            lines.extend(
                f"- {item['name']} ({item['calories']} kcal, score {item['nutrition_score']})"
                for item in selected
            )
            show_card("Optimized grocery list", "<br>".join(lines))
        else:
            st.error(data["error"])
    else:
        st.warning("Please add some items first.")
