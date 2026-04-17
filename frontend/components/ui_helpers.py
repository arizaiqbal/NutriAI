import streamlit as st


def show_bmi_card(user: dict):
    """
    Displays a styled BMI + calorie summary card.
    Used on the registration success screen and profile view.
    """
    bmi      = user.get("bmi", 0)
    category = user.get("bmi_category", "")

    # pick colour based on BMI category
    color_map = {
        "Underweight": "🔵",
        "Normal weight": "🟢",
        "Overweight":   "🟡",
        "Obese":        "🔴",
    }
    icon = color_map.get(category, "⚪")

    st.markdown("### Your Health Summary")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label=f"{icon} BMI", value=bmi)
        st.caption(category)

    with col2:
        st.metric(
            label="🔥 Daily Calories",
            value=f"{user.get('daily_calories', 0)} kcal"
        )

    with col3:
        st.metric(
            label="🎯 Goal",
            value=user.get("goal", "").capitalize()
        )


def show_macro_breakdown(user: dict):
    """
    Displays protein / carbs / fat targets as three columns.
    """
    st.markdown("### Daily Macro Targets")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("💪 Protein", f"{user.get('protein_g', 0)}g")
    with col2:
        st.metric("🌾 Carbs", f"{user.get('carbs_g', 0)}g")
    with col3:
        st.metric("🥑 Fat", f"{user.get('fat_g', 0)}g")


def show_error(message: str):
    """Displays a red error box."""
    st.error(f"❌ {message}")


def show_success(message: str):
    """Displays a green success box."""
    st.success(f"✅ {message}")


def require_login():
    """
    Checks if a user is logged in via session state.
    If not, shows a warning and stops the page from rendering further.
    Call this at the top of any page that requires a logged-in user.

    Usage:
        user = require_login()
        if not user:
            st.stop()
    
    Returns the user dict if logged in, None otherwise.
    """
    user = st.session_state.get("user")
    if not user:
        st.warning("⚠️ Please register or log in first.")
        st.page_link("pages/Register.py", label="Go to Registration →")
        return None
    return user
