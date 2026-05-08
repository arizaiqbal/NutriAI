import os
import sys

import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from frontend.components.ui_helpers import apply_theme, show_card, show_feature_grid


st.set_page_config(
    page_title="NutriAI",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "user" not in st.session_state:
    st.session_state["user"] = None

if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = []

if "meal_plan" not in st.session_state:
    st.session_state["meal_plan"] = None

if "nutrition_logs" not in st.session_state:
    st.session_state["nutrition_logs"] = []

with st.sidebar:
    st.markdown("## NutriAI")
    st.divider()

    user = st.session_state.get("user")
    if user:
        st.markdown(f"**{user.get('name', 'User')}**")
        st.caption(user.get("email", ""))
        st.caption(f"Goal: {user.get('goal', '').capitalize()}")
        st.divider()

        if st.button("Logout", use_container_width=True):
            st.session_state["user"] = None
            st.session_state["chat_messages"] = []
            st.session_state["meal_plan"] = None
            st.session_state["nutrition_logs"] = []
            st.rerun()
    else:
        st.info("Not logged in")

apply_theme(
    "Welcome to NutriAI",
    "A more colorful, cozy nutrition dashboard for meal planning, logging, chat, and everyday healthy habits.",
    badge="Glow Mode",
)

show_feature_grid([
    ("Meal Plans", "7-day guidance"),
    ("Nutrition Log", "Daily food tracking"),
    ("AI Chat", "Ask anything"),
    ("HealthyOrNot", "Quick insights"),
])

col1, col2 = st.columns([1.2, 1])
with col1:
    show_card(
        "Your pastel nutrition corner",
        "Build meal plans, explore ingredient-based ideas, keep a food log, and ask nutrition questions in one softer, more visually cheerful space.",
    )

with col2:
    if st.session_state.get("user"):
        user = st.session_state["user"]
        show_card(
            "Current snapshot",
            f"Logged in as <strong>{user.get('name', 'User')}</strong><br>Goal: <strong>{user.get('goal', '').capitalize()}</strong><br>Daily target: <strong>{user.get('daily_calories', 0)} kcal</strong>",
        )
    else:
        show_card(
            "Quick start",
            "Open the Register page from the sidebar to create your profile and unlock all the personalized parts of the app.",
        )

if not st.session_state.get("user"):
    st.info("Start by registering your profile using the sidebar.")
else:
    name = st.session_state["user"].get("name", "")
    st.success(f"Welcome back, {name}! Use the sidebar to navigate.")
