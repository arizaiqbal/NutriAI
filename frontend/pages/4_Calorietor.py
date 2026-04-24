import os
import sys

import requests
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from frontend.components.api_client import get_meal_health_score
from frontend.components.ui_helpers import apply_theme, show_card, show_feature_grid


st.set_page_config(page_title="HealthyOrNot - NutriAI", page_icon="🌈")

apply_theme(
    "HealthyOrNot",
    "Play with calories and macros to see how the model classifies a meal and estimates your daily calorie needs.",
    badge="ML Playground",
)
show_card("Nutrition Insights", "Two cute little tools live here: a calorie prediction model and a meal health classifier.")

st.subheader("Predict the calorie intake you need for today")
col1, col2 = st.columns(2)
with col1:
    weight = st.number_input("Weight (kg)", 30, 200, 65)
    height = st.number_input("Height (cm)", 100, 220, 165)
    age = st.number_input("Age", 10, 100, 25)
with col2:
    gender = st.selectbox("Gender", ["female", "male"])
    activity = st.selectbox("Activity Level Today", [1, 2, 3], format_func=lambda x: {1: "Low", 2: "Moderate", 3: "High"}[x])

if st.button("Predict with ML Model", use_container_width=True):
    response = requests.post(
        "http://localhost:5000/api/meal/ml-predict",
        json={"weight": weight, "height": height, "age": age, "gender": gender, "activity_level": activity},
    )
    if response.ok:
        data = response.json()
        st.success(f"ML Predicted Calories: {data['ml_predicted_calories']} kcal/day")
        show_feature_grid([
            ("Prediction", f"{data['ml_predicted_calories']} kcal/day"),
            ("Model", data["model_info"].get("type", "ML")),
        ])
        with st.expander("Model Info"):
            st.json(data["model_info"])

st.divider()
st.subheader("Food Health Score")
cal = st.number_input("Calories", 0, 2000, 400)
protein = st.number_input("Protein (g)", 0, 200, 20)
carbs = st.number_input("Carbs (g)", 0, 300, 50)
fat = st.number_input("Fat (g)", 0, 100, 15)

if st.button("Get Health Score", use_container_width=True):
    data = get_meal_health_score(cal, protein, carbs, fat)
    if "error" not in data:
        score = data["health_score"]
        label = data["label"]
        color = "green" if label == "Healthy" else "orange" if label == "Moderate" else "red"
        st.markdown(f"### Score: **:{color}[{score}/100 - {label}]**")
        show_feature_grid([
            ("Calories", f"{cal} kcal"),
            ("Protein", f"{protein} g"),
            ("Carbs", f"{carbs} g"),
            ("Fat", f"{fat} g"),
        ])
