import streamlit as st
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from frontend.components.api_client import register_user, get_profile
from frontend.components.ui_helpers import show_bmi_card, show_macro_breakdown, show_error, show_success


def reset_user_session_state():
    """Clear user-specific cached data before switching users."""
    st.session_state["chat_messages"] = []
    st.session_state["meal_plan"] = None
    st.session_state["nutrition_logs"] = []

st.set_page_config(page_title="Register — NutriAI", page_icon="📋")
st.title("📋 Register / Login")

# ── tabs: two modes on the same page ───────────────────────────────────────
tab_register, tab_login = st.tabs(["New User — Register", "Returning User — Login"])


# ── TAB 1: REGISTRATION ────────────────────────────────────────────────────
with tab_register:
    st.markdown("Fill in your details and we'll calculate your BMI and calorie targets.")

    with st.form("registration_form"):
        col1, col2 = st.columns(2)

        with col1:
            name       = st.text_input("Full Name")
            email      = st.text_input("Email Address")
            age        = st.number_input("Age", min_value=10, max_value=100, value=20)
            gender     = st.selectbox("Gender", ["female", "male"])

        with col2:
            height_cm  = st.number_input("Height (cm)", min_value=100.0, max_value=250.0, value=165.0)
            weight_kg  = st.number_input("Weight (kg)", min_value=30.0,  max_value=300.0, value=60.0)
            goal       = st.selectbox("Diet Goal", ["maintenance", "loss", "gain"])
            activity   = st.selectbox(
                "Activity Level",
                ["sedentary", "light", "moderate", "active"],
                index=2
            )

        restrictions = st.text_input(
            "Dietary Restrictions",
            placeholder="e.g. vegetarian, gluten-free, nut allergy — or type 'none'"
        )

        submitted = st.form_submit_button("Register", use_container_width=True)

    # ── handle form submission ──────────────────────────────────────────────
    if submitted:
        # basic client-side validation
        if not name or not email:
            show_error("Name and email are required.")
        else:
            with st.spinner("Calculating your nutritional profile..."):
                result = register_user({
                    "name":           name,
                    "email":          email,
                    "age":            age,
                    "gender":         gender,
                    "height_cm":      height_cm,
                    "weight_kg":      weight_kg,
                    "goal":           goal,
                    "activity_level": activity,
                    "restrictions":   restrictions or "none",
                })

            if "error" in result:
                show_error(result["error"])
            else:
                # save user to session state so all pages can access it
                reset_user_session_state()
                st.session_state["user"] = result.get("user", result)
                show_success("Registration successful!")
                show_bmi_card(st.session_state["user"])
                show_macro_breakdown(st.session_state["user"])


# ── TAB 2: LOGIN ───────────────────────────────────────────────────────────
with tab_login:
    st.markdown("Already registered? Enter your email to reload your profile.")

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
                st.session_state["user"] = result
                show_success(f"Welcome back, {result.get('name', '')}!")
                show_bmi_card(result)
                show_macro_breakdown(result)
