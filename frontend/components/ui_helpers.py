import streamlit as st


def apply_theme(page_title: str, subtitle: str = "", badge: str = "NutriAI"):
    st.markdown(
        """
        <style>
        :root {
            --ink: #31263b;
            --muted: #74657d;
            --card: rgba(255, 255, 255, 0.82);
            --border: rgba(255, 255, 255, 0.58);
            --shadow: 0 24px 60px rgba(222, 179, 190, 0.22);
        }
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(255, 221, 233, 0.95), transparent 28%),
                radial-gradient(circle at top right, rgba(226, 250, 219, 0.95), transparent 26%),
                radial-gradient(circle at bottom center, rgba(223, 241, 255, 0.95), transparent 34%),
                linear-gradient(180deg, #fff9f4 0%, #f8f4ff 48%, #fffdf8 100%);
            color: var(--ink);
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(255,255,255,0.88), rgba(255,245,249,0.92));
            border-right: 1px solid rgba(255,255,255,0.6);
            backdrop-filter: blur(16px);
        }
        [data-testid="stHeader"] { background: transparent; }
        div[data-testid="stMetric"], div[data-testid="stForm"] {
            background: linear-gradient(180deg, rgba(255,255,255,0.92), rgba(255,248,251,0.88));
            border: 1px solid var(--border);
            border-radius: 26px;
            box-shadow: var(--shadow);
        }
        div[data-testid="stMetric"] { padding: 1rem 1.1rem; }
        div[data-testid="stForm"] { padding: 1rem 1rem 0.4rem 1rem; }
        .stButton > button, div[data-testid="stFormSubmitButton"] button {
            border-radius: 999px !important;
            border: none !important;
            color: #5d3654 !important;
            font-weight: 700 !important;
            background: linear-gradient(90deg, #ffd0dd, #ffe3af, #d7f3af) !important;
            box-shadow: 0 14px 32px rgba(246, 179, 164, 0.28) !important;
        }
        div[data-testid="stTextInput"] > div > div,
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stNumberInput"] input,
        div[data-baseweb="select"] > div {
            border-radius: 18px !important;
            border: 1px solid rgba(255, 210, 223, 0.88) !important;
            background: rgba(255,255,255,0.92) !important;
        }
        .stTabs [data-baseweb="tab-list"] { gap: 0.55rem; }
        .stTabs [data-baseweb="tab"] {
            border-radius: 999px;
            background: rgba(255,255,255,0.66);
            padding: 0.5rem 1rem;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(90deg, #ffdbe7, #fff1b8) !important;
            color: #5d3654 !important;
        }
        div[data-testid="stChatMessage"] {
            background: rgba(255,255,255,0.72);
            border: 1px solid rgba(255,255,255,0.5);
            border-radius: 24px;
            box-shadow: 0 16px 36px rgba(205, 185, 214, 0.18);
        }
        .nutri-hero {
            background:
                radial-gradient(circle at top right, rgba(255,255,255,0.82), transparent 28%),
                linear-gradient(135deg, rgba(255, 229, 238, 0.96), rgba(225, 248, 224, 0.94) 54%, rgba(223, 242, 255, 0.96));
            border: 1px solid rgba(255,255,255,0.62);
            border-radius: 34px;
            padding: 1.35rem 1.5rem;
            margin-bottom: 1.1rem;
            box-shadow: var(--shadow);
        }
        .nutri-badge {
            display: inline-block;
            background: rgba(255,255,255,0.72);
            color: #7a5066;
            border-radius: 999px;
            padding: 0.28rem 0.82rem;
            font-size: 0.84rem;
            font-weight: 700;
            margin-bottom: 0.55rem;
        }
        .nutri-title {
            font-size: 2.15rem;
            line-height: 1.06;
            font-weight: 800;
            color: var(--ink);
            margin-bottom: 0.35rem;
        }
        .nutri-subtitle {
            color: var(--muted);
            font-size: 1rem;
            max-width: 760px;
        }
        .nutri-card {
            background: linear-gradient(180deg, rgba(255,255,255,0.92), rgba(255,249,252,0.84));
            border: 1px solid var(--border);
            border-radius: 28px;
            box-shadow: var(--shadow);
            padding: 1rem 1.1rem;
            margin-bottom: 1rem;
        }
        .nutri-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 0.8rem;
            margin: 0.75rem 0 1.1rem 0;
        }
        .nutri-pill {
            background: rgba(255,255,255,0.8);
            border-radius: 22px;
            border: 1px solid rgba(255,255,255,0.58);
            padding: 0.82rem 0.95rem;
            box-shadow: 0 12px 28px rgba(205, 176, 189, 0.16);
        }
        .nutri-pill-label {
            color: var(--muted);
            font-size: 0.84rem;
            margin-bottom: 0.24rem;
        }
        .nutri-pill-value {
            color: var(--ink);
            font-size: 1.12rem;
            font-weight: 800;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="nutri-hero">
            <div class="nutri-badge">{badge}</div>
            <div class="nutri-title">{page_title}</div>
            <div class="nutri-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_feature_grid(items):
    html = []
    for label, value in items:
        html.append(
            f"<div class='nutri-pill'><div class='nutri-pill-label'>{label}</div><div class='nutri-pill-value'>{value}</div></div>"
        )
    st.markdown(f"<div class='nutri-grid'>{''.join(html)}</div>", unsafe_allow_html=True)


def show_card(title: str, body: str):
    st.markdown(
        f"<div class='nutri-card'><h3>{title}</h3><p style='margin-top:0.45rem;color:#74657d;'>{body}</p></div>",
        unsafe_allow_html=True,
    )


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
