import os
import sys

import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from frontend.components.api_client import create_nutrition_log, get_nutrition_logs
from frontend.components.ui_helpers import require_login, show_error, show_success

st.set_page_config(page_title="Nutrition Log - NutriAI", page_icon="📊")
st.title("📊 Nutrition Log")

user = require_login()
if not user:
    st.stop()

if "nutrition_logs" not in st.session_state:
    st.session_state["nutrition_logs"] = []

st.markdown("Describe a meal or food in plain English and save its estimated nutrition to your log.")

if not st.session_state["nutrition_logs"]:
    history = get_nutrition_logs(user["email"])
    if "logs" in history:
        st.session_state["nutrition_logs"] = history["logs"]

with st.form("log_form"):
    food_description = st.text_input(
        "What did you eat?",
        placeholder="e.g. 2 boiled eggs and a slice of whole wheat toast with butter"
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
            st.divider()
            st.markdown("### Estimated Nutrition")
            st.markdown(f"**Food:** {food_description}")
            st.markdown(result["reply"])

            if result.get("log"):
                st.session_state["nutrition_logs"] = [result["log"], *st.session_state["nutrition_logs"]]

            st.divider()
            st.markdown("### How This Fits Your Day")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Your daily target", f"{user.get('daily_calories', 0)} kcal")
            with col2:
                st.caption("Log more meals to track your total intake.")

st.divider()
st.markdown("### Recent Entries")
if st.session_state["nutrition_logs"]:
    for entry in st.session_state["nutrition_logs"][:10]:
        st.markdown(
            f"**{entry.get('date', '')}**  \n"
            f"{entry.get('food_description', '')}  \n"
            f"{entry.get('calories', 0)} kcal | "
            f"P {entry.get('protein_g', 0)}g | "
            f"C {entry.get('carbs_g', 0)}g | "
            f"F {entry.get('fat_g', 0)}g"
        )
else:
    st.info("No nutrition log entries yet.")
