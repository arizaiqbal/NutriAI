import os
import sys

import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from frontend.components.api_client import get_profile, register_user
from frontend.components.ui_helpers import (
    apply_theme,
    show_bmi_card,
    show_card,
    show_error,
    show_feature_grid,
    show_macro_breakdown,
    show_success,
)


def reset_user_session_state():
    st.session_state["chat_messages"] = []
    st.session_state["meal_plan"] = None
    st.session_state["nutrition_logs"] = []


def show_email_result(email_result, success_default):
    if email_result.get("sent"):
        show_success(email_result.get("message", success_default))
    elif email_result:
        show_error(email_result.get("message", "Email notification failed."))


st.set_page_config(page_title="Register - NutriAI", page_icon="📋")

apply_theme(
    "Register / Login",
    "Create your wellness profile, calculate your targets, and jump back into your saved setup whenever you want.",
    badge="Profile Setup",
)

show_feature_grid([
    ("BMI", "Auto summary"),
    ("Calories", "Daily target"),
    ("Macros", "Protein, carbs, fat"),
])

tab_register, tab_login = st.tabs(["New User - Register", "Returning User - Login"])

with tab_register:
    show_card("Create your profile", "Fill in your details and NutriAI will calculate your BMI, calories, and macros for you.")

    with st.form("registration_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Full Name")
            email = st.text_input("Email Address")
            age = st.number_input("Age", min_value=10, max_value=100, value=20)
            gender = st.selectbox("Gender", ["female", "male"])

        with col2:
            height_cm = st.number_input("Height (cm)", min_value=100.0, max_value=250.0, value=165.0)
            weight_kg = st.number_input("Weight (kg)", min_value=30.0, max_value=300.0, value=60.0)
            goal = st.selectbox("Diet Goal", ["maintenance", "loss", "gain"])
            activity = st.selectbox("Activity Level", ["sedentary", "light", "moderate", "active"], index=2)

        restrictions = st.text_input(
            "Dietary Restrictions",
            placeholder="e.g. vegetarian, gluten-free, nut allergy - or type 'none'",
        )

        submitted = st.form_submit_button("Register", use_container_width=True)

    if submitted:
        if not name or not email:
            show_error("Name and email are required.")
        else:
            with st.spinner("Calculating your nutritional profile..."):
                result = register_user({
                    "name": name,
                    "email": email,
                    "age": age,
                    "gender": gender,
                    "height_cm": height_cm,
                    "weight_kg": weight_kg,
                    "goal": goal,
                    "activity_level": activity,
                    "restrictions": restrictions or "none",
                })

            if "error" in result:
                show_error(result["error"])
            else:
                reset_user_session_state()
                st.session_state["user"] = result.get("user", result)
                show_success("Registration successful!")
                if result.get("notification"):
                    st.info(result["notification"])
                show_email_result(
                    result.get("email_notification", {}),
                    "Registration email notification sent.",
                )
                show_bmi_card(st.session_state["user"])
                show_macro_breakdown(st.session_state["user"])

with tab_login:
    show_card("Welcome back", "Reload your saved profile and jump right back into the app.")
    login_email = st.text_input("Email Address", key="login_email")

    if st.button("Load My Profile", use_container_width=True):
        if not login_email:
            show_error("Please enter your email.")
        else:
            with st.spinner("Loading your profile..."):
                result = get_profile(login_email)

            if "error" in result:
                show_error(result["error"])
            else:
                reset_user_session_state()
                user = result.get("user", result)
                st.session_state["user"] = user
                show_success(f"Welcome back, {user.get('name', '')}!")
                if result.get("notification"):
                    st.info(result["notification"])
                show_email_result(
                    result.get("email_notification", {}),
                    "Login reminder email notification sent.",
                )
                show_bmi_card(user)
                show_macro_breakdown(user)
