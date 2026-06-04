import html

import altair as alt
import pandas as pd
import streamlit as st


MACRO_COLORS = {
    "Protein": "#4f46e5",
    "Carbs": "#ff7a59",
    "Fat": "#18b7a6",
    "Calories": "#7c3aed",
}


def apply_theme(page_title: str, subtitle: str = "", badge: str = "NutriAI"):
    st.markdown(
        """
        <style>
        :root {
            --ink: #20143f;
            --muted: #6f6385;
            --purple: #5b38d6;
            --deep-purple: #32127a;
            --lavender: #d9d1ff;
            --coral: #ff7a59;
            --mint: #18b7a6;
            --sun: #ffc857;
            --card: rgba(255, 255, 255, 0.9);
            --border: rgba(120, 94, 214, 0.16);
            --shadow: 0 22px 48px rgba(70, 49, 150, 0.18);
        }
        .stApp {
            background:
                linear-gradient(135deg, rgba(255,255,255,0.28) 0 12%, transparent 12% 24%, rgba(255,255,255,0.18) 24% 36%, transparent 36% 100%),
                linear-gradient(180deg, #cec4ff 0%, #eee9ff 42%, #fbf8ff 100%);
            color: var(--ink);
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(67,39,158,0.94), rgba(42,22,111,0.96));
            border-right: 1px solid rgba(255,255,255,0.16);
            backdrop-filter: blur(16px);
        }
        [data-testid="stSidebar"] * { color: rgba(255,255,255,0.92) !important; }
        [data-testid="stSidebar"] .stButton > button {
            background: rgba(255,255,255,0.14) !important;
            color: #ffffff !important;
            box-shadow: none !important;
        }
        [data-testid="stHeader"] { background: transparent; }
        div[data-testid="stMetric"], div[data-testid="stForm"] {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 8px;
            box-shadow: var(--shadow);
        }
        div[data-testid="stMetric"] { padding: 1rem 1.1rem; }
        div[data-testid="stForm"] { padding: 1rem 1rem 0.4rem 1rem; }
        .stButton > button, div[data-testid="stFormSubmitButton"] button {
            border-radius: 999px !important;
            border: none !important;
            color: #ffffff !important;
            font-weight: 700 !important;
            background: linear-gradient(90deg, var(--deep-purple), var(--purple), var(--coral)) !important;
            box-shadow: 0 14px 28px rgba(91, 56, 214, 0.28) !important;
        }
        div[data-testid="stTextInput"] > div > div,
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stNumberInput"] input,
        div[data-baseweb="select"] > div {
            border-radius: 8px !important;
            border: 1px solid rgba(120, 94, 214, 0.2) !important;
            background: rgba(255,255,255,0.96) !important;
        }
        .stTabs [data-baseweb="tab-list"] { gap: 0.55rem; }
        .stTabs [data-baseweb="tab"] {
            border-radius: 999px;
            background: rgba(255,255,255,0.78);
            padding: 0.5rem 1rem;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(90deg, var(--deep-purple), var(--purple)) !important;
            color: #ffffff !important;
        }
        div[data-testid="stChatMessage"] {
            background: rgba(255,255,255,0.88);
            border: 1px solid var(--border);
            border-radius: 8px;
            box-shadow: 0 16px 36px rgba(70, 49, 150, 0.12);
        }
        .nutri-hero {
            background:
                linear-gradient(90deg, rgba(255,255,255,0.16) 0 1px, transparent 1px 100%),
                linear-gradient(135deg, #38158f 0%, #6040d9 48%, #ff7a59 100%);
            background-size: 22px 22px, auto;
            border: 1px solid rgba(255,255,255,0.34);
            border-radius: 8px;
            padding: 1.55rem 1.6rem;
            margin-bottom: 1.1rem;
            box-shadow: var(--shadow);
        }
        .nutri-badge {
            display: inline-block;
            background: rgba(255,255,255,0.16);
            color: #ffffff;
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
            color: #ffffff;
            margin-bottom: 0.35rem;
        }
        .nutri-subtitle {
            color: rgba(255,255,255,0.82);
            font-size: 1rem;
            max-width: 760px;
        }
        .nutri-card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 8px;
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
            background: rgba(255,255,255,0.9);
            border-radius: 8px;
            border: 1px solid var(--border);
            padding: 0.82rem 0.95rem;
            box-shadow: 0 12px 28px rgba(70, 49, 150, 0.1);
            border-top: 4px solid var(--coral);
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
        .nutri-card h3 { margin-top: 0; color: var(--ink); }
        .macro-shell {
            background: rgba(255,255,255,0.9);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem;
            box-shadow: var(--shadow);
            margin-bottom: 1rem;
        }
        .macro-shell h3 {
            margin: 0 0 0.25rem 0;
            font-size: 1.15rem;
            color: var(--ink);
        }
        .macro-shell p {
            color: var(--muted);
            margin: 0 0 0.8rem 0;
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
        f"<div class='nutri-card'><h3>{html.escape(title)}</h3><p style='margin-top:0.45rem;color:#6f6385;'>{body}</p></div>",
        unsafe_allow_html=True,
    )


def _macro_dataframe(protein=0, carbs=0, fat=0):
    values = [
        ("Protein", float(protein or 0)),
        ("Carbs", float(carbs or 0)),
        ("Fat", float(fat or 0)),
    ]
    return pd.DataFrame(values, columns=["Macro", "Grams"])


def show_macro_charts(protein=0, carbs=0, fat=0, title="Macro Breakdown", subtitle="Protein, carbs, and fat shown as grams."):
    df = _macro_dataframe(protein, carbs, fat)
    if df["Grams"].sum() <= 0:
        return

    st.markdown(
        f"<div class='macro-shell'><h3>{html.escape(title)}</h3><p>{html.escape(subtitle)}</p></div>",
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns([1.15, 1])
    with col1:
        bar_chart = (
            alt.Chart(df)
            .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
            .encode(
                x=alt.X("Macro:N", sort=["Protein", "Carbs", "Fat"], axis=alt.Axis(labelAngle=0, title=None)),
                y=alt.Y("Grams:Q", axis=alt.Axis(title="grams")),
                color=alt.Color(
                    "Macro:N",
                    scale=alt.Scale(domain=list(MACRO_COLORS.keys())[:3], range=list(MACRO_COLORS.values())[:3]),
                    legend=None,
                ),
                tooltip=["Macro", alt.Tooltip("Grams:Q", format=".0f")],
            )
            .properties(height=230)
        )
        st.altair_chart(bar_chart, use_container_width=True)

    with col2:
        donut_chart = (
            alt.Chart(df)
            .mark_arc(innerRadius=62, outerRadius=104, cornerRadius=5)
            .encode(
                theta=alt.Theta("Grams:Q"),
                color=alt.Color(
                    "Macro:N",
                    scale=alt.Scale(domain=list(MACRO_COLORS.keys())[:3], range=list(MACRO_COLORS.values())[:3]),
                    legend=alt.Legend(orient="bottom", title=None),
                ),
                tooltip=["Macro", alt.Tooltip("Grams:Q", format=".0f")],
            )
            .properties(height=230)
        )
        st.altair_chart(donut_chart, use_container_width=True)


def show_nutrition_snapshot(calories=0, protein=0, carbs=0, fat=0, title="Food Nutrition Snapshot"):
    st.markdown(
        f"<div class='macro-shell'><h3>{html.escape(title)}</h3><p>Calories plus macro grams in one quick visual view.</p></div>",
        unsafe_allow_html=True,
    )
    metrics = pd.DataFrame(
        [
            ("Calories", float(calories or 0)),
            ("Protein", float(protein or 0)),
            ("Carbs", float(carbs or 0)),
            ("Fat", float(fat or 0)),
        ],
        columns=["Metric", "Value"],
    )
    chart = (
        alt.Chart(metrics)
        .mark_bar(cornerRadius=6)
        .encode(
            x=alt.X("Value:Q", axis=alt.Axis(title=None)),
            y=alt.Y("Metric:N", sort=["Calories", "Protein", "Carbs", "Fat"], axis=alt.Axis(title=None)),
            color=alt.Color(
                "Metric:N",
                scale=alt.Scale(domain=list(MACRO_COLORS.keys()), range=list(MACRO_COLORS.values())),
                legend=None,
            ),
            tooltip=["Metric", alt.Tooltip("Value:Q", format=".0f")],
        )
        .properties(height=210)
    )
    st.altair_chart(chart, use_container_width=True)


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

    show_macro_charts(
        user.get("protein_g", 0),
        user.get("carbs_g", 0),
        user.get("fat_g", 0),
        title="Daily Macro Balance",
        subtitle="Your personalized protein, carb, and fat targets as a bar chart and donut chart.",
    )


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
