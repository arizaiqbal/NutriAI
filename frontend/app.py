import streamlit as st

# ── page config must be the very first Streamlit call ──────────────────────
st.set_page_config(
    page_title = "NutriAI",
    page_icon  = "🥗",
    layout     = "wide",
    initial_sidebar_state = "expanded",
)

# ── initialise session state keys so pages never get KeyError ──────────────
# These are set once here; pages read and write them freely.
if "user"          not in st.session_state:
    st.session_state["user"] = None          # holds the full user dict when logged in

if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = []   # list of {role, message} dicts for chat UI

if "meal_plan"     not in st.session_state:
    st.session_state["meal_plan"] = None     # latest generated plan text

if "nutrition_logs" not in st.session_state:
    st.session_state["nutrition_logs"] = []  # saved nutrition log entries for the active user

# ── sidebar: show logged-in user info if available ─────────────────────────
with st.sidebar:
    st.markdown("## 🥗 NutriAI")
    st.divider()

    user = st.session_state.get("user")
    if user:
        st.markdown(f"**👤 {user.get('name', 'User')}**")
        st.caption(user.get("email", ""))
        st.caption(f"Goal: {user.get('goal', '').capitalize()}")
        st.divider()

        # logout button clears the session
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state["user"]          = None
            st.session_state["chat_messages"] = []
            st.session_state["meal_plan"]     = None
            st.session_state["nutrition_logs"] = []
            st.rerun()
    else:
        st.info("Not logged in")

# ── home page content ───────────────────────────────────────────────────────
st.title("Welcome to NutriAI 🥗")
st.markdown("""
Your AI-powered personal nutrition assistant.

**What NutriAI can do for you:**
- Calculate your BMI and daily calorie needs
- Generate personalised 7-day meal plans
- Suggest meals from ingredients you already have
- Answer any nutrition question via AI chat
- Build your weekly grocery list automatically
""")

if not st.session_state.get("user"):
    st.info("👈 Start by registering your profile using the sidebar.")
else:
    name = st.session_state["user"].get("name", "")
    st.success(f"Welcome back, {name}! Use the sidebar to navigate.")
