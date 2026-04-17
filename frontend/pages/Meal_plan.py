import streamlit as st
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from frontend.components.api_client import (
    generate_meal_plan,
    get_latest_meal_plan,
    suggest_from_ingredients,
    generate_grocery_list,
)
from frontend.components.ui_helpers import require_login, show_error, show_success

st.set_page_config(page_title="Meal Plan — NutriAI", page_icon="🍽️")
st.title("🍽️ Meal Planning")

user = require_login()
if not user:
    st.stop()

# ── three tabs for three features ─────────────────────────────────────────
tab_plan, tab_ingredients, tab_grocery = st.tabs([
    "📅 7-Day Meal Plan",
    "🥦 Ingredient-Based Suggestions",
    "🛒 Grocery List"
])


# ── TAB 1: MEAL PLAN ──────────────────────────────────────────────────────
with tab_plan:
    st.markdown(f"Generate a personalised plan targeting **{user.get('daily_calories')} kcal/day**.")

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("🔄 Generate New Meal Plan", use_container_width=True):
            with st.spinner("Building your 7-day plan..."):
                result = generate_meal_plan(user["email"])

            if "error" in result:
                show_error(result["error"])
            else:
                st.session_state["meal_plan"] = result["meal_plan"]
                show_success("Meal plan generated and saved!")

    with col2:
        if st.button("📂 Load Saved Plan", use_container_width=True):
            with st.spinner("Loading your latest plan..."):
                result = get_latest_meal_plan(user["email"])

            if "error" in result:
                show_error(result.get("error", "No saved plan found."))
            else:
                st.session_state["meal_plan"] = result.get("meal_plan", "")
                if result.get("week_start"):
                    st.caption(f"Plan from: {result['week_start']}")

    # display the plan if it exists in session
    if st.session_state.get("meal_plan"):
        st.divider()
        st.markdown("### Your 7-Day Plan")
        st.markdown(st.session_state["meal_plan"])


# ── TAB 2: INGREDIENT SUGGESTIONS ────────────────────────────────────────
with tab_ingredients:
    st.markdown("Enter what you have at home and get matching meal ideas.")

    ingredient_input = st.text_area(
        "Available Ingredients",
        placeholder="chicken, spinach, garlic, olive oil, tomatoes, onion",
        height=100,
    )

    if st.button("🔍 Find Meals", use_container_width=True):
        if not ingredient_input.strip():
            show_error("Please enter at least one ingredient.")
        else:
            # split by comma, strip whitespace, remove empty strings
            ingredients = [i.strip() for i in ingredient_input.split(",") if i.strip()]

            with st.spinner(f"Searching for meals using {len(ingredients)} ingredients..."):
                result = suggest_from_ingredients(user["email"], ingredients)

            if "error" in result:
                show_error(result["error"])
            else:
                st.divider()
                st.markdown("### Suggested Meals")
                st.markdown(result["suggestions"])


# ── TAB 3: GROCERY LIST ───────────────────────────────────────────────────
with tab_grocery:
    st.markdown("Generate a grocery list based on your latest saved meal plan.")

    if not st.session_state.get("meal_plan"):
        st.info("💡 Generate or load a meal plan first (in the first tab), then come back here.")

    if st.button("🛒 Generate Grocery List", use_container_width=True):
        with st.spinner("Building your grocery list..."):
            result = generate_grocery_list(user["email"])

        if "error" in result:
            show_error(result["error"])
        else:
            st.divider()
            st.markdown("### Your Grocery List")
            st.markdown(result["grocery_list"])