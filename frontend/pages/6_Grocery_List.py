import os
import sys

import requests
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from frontend.components.api_client import optimize_grocery_items
from frontend.components.ui_helpers import apply_theme, show_card


st.set_page_config(page_title="Grocery List - NutriAI", page_icon="🛒")

apply_theme(
    "Grocery List",
    "Generate a shopping list from a meal plan or optimize item choices with a colorful little planner.",
    badge="Pantry Pop",
)

show_card("Generate from meal plan", "Paste a plan to get a grocery list, or use the optimizer below to choose the best items inside a calorie budget.")

meal_plan = st.text_area("Paste your meal plan here:", height=200)

if st.button("Generate Grocery List", use_container_width=True):
    if meal_plan:
        with st.spinner("Generating..."):
            response = requests.post(
                "http://localhost:5000/api/meal/grocery-list",
                json={"meal_plan": meal_plan},
            )
        if response.ok:
            show_card("Your grocery list", response.json()["grocery_list"])
    else:
        st.warning("Please paste a meal plan first.")

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
                f"Algorithm: {data.get('algorithm', '0/1 Knapsack Dynamic Programming')}",
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
