import os
import sys

import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from frontend.components.api_client import create_nutrition_log, get_nutrition_logs
from frontend.components.ui_helpers import (
    apply_theme,
    require_login,
    show_card,
    show_error,
    show_feature_grid,
    show_macro_charts,
    show_nutrition_snapshot,
    show_success,
)


st.set_page_config(page_title="Nutrition Log - NutriAI", page_icon="📊")

apply_theme(
    "Nutrition Log",
    "Keep a cute running diary of meals, calories, and macros without losing the helpful structure.",
    badge="Nutrition Tracking",
)

user = require_login()
if not user:
    st.stop()

if "nutrition_logs" not in st.session_state:
    st.session_state["nutrition_logs"] = []

show_feature_grid([
    ("Daily target", f"{user.get('daily_calories', 0)} kcal"),
    ("Saved entries", str(len(st.session_state["nutrition_logs"]))),
])
show_card("Log a meal", "Describe a food or meal in plain English and save its estimated nutrition to your history.")

if not st.session_state["nutrition_logs"]:
    history = get_nutrition_logs(user["email"])
    if "logs" in history:
        st.session_state["nutrition_logs"] = history["logs"]

with st.form("log_form"):
    food_description = st.text_input(
        "What did you eat?",
        placeholder="e.g. 2 boiled eggs and a slice of whole wheat toast with butter",
    )
    log_submitted = st.form_submit_button("Estimate and Save", use_container_width=True)

if log_submitted:
    if not food_description.strip():
        show_error("Please describe what you ate.")
    else:
        with st.spinner("Estimating nutrition..."):
            result = create_nutrition_log(user["email"], food_description)

        if "error" in result:
            show_error(result["error"])
        else:
            show_success("Nutrition estimated and saved!")
            show_card("Estimated nutrition", f"<strong>Food:</strong> {food_description}<br><br>{result['reply']}")

            if result.get("log"):
                st.session_state["nutrition_logs"] = [result["log"], *st.session_state["nutrition_logs"]]
                log = result["log"]
                show_nutrition_snapshot(
                    log.get("calories", 0),
                    log.get("protein_g", 0),
                    log.get("carbs_g", 0),
                    log.get("fat_g", 0),
                    title="Estimated Meal Visual",
                )

st.markdown("### Recent Entries")
if st.session_state["nutrition_logs"]:
    recent = st.session_state["nutrition_logs"][:10]
    total_calories = sum(float(entry.get("calories", 0) or 0) for entry in recent)
    total_protein = sum(float(entry.get("protein_g", 0) or 0) for entry in recent)
    total_carbs = sum(float(entry.get("carbs_g", 0) or 0) for entry in recent)
    total_fat = sum(float(entry.get("fat_g", 0) or 0) for entry in recent)
    show_feature_grid([
        ("Recent calories", f"{total_calories:.0f} kcal"),
        ("Recent protein", f"{total_protein:.0f} g"),
        ("Recent carbs", f"{total_carbs:.0f} g"),
        ("Recent fat", f"{total_fat:.0f} g"),
    ])
    show_macro_charts(
        total_protein,
        total_carbs,
        total_fat,
        title="Recent Macro Mix",
        subtitle="Macro totals from your latest saved food entries.",
    )
    for entry in st.session_state["nutrition_logs"][:10]:
        show_card(
            entry.get("date", "Entry"),
            f"{entry.get('food_description', '')}<br><br>{entry.get('calories', 0)} kcal | P {entry.get('protein_g', 0)}g | C {entry.get('carbs_g', 0)}g | F {entry.get('fat_g', 0)}g",
        )
else:
    st.info("No nutrition log entries yet.")
