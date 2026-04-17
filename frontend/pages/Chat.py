import streamlit as st
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from frontend.components.api_client import send_chat_message, get_chat_history
from frontend.components.ui_helpers import require_login, show_error

st.set_page_config(page_title="Chat — NutriAI", page_icon="💬")
st.title("💬 Chat with NutriAI")

# ── guard: stop if not logged in ───────────────────────────────────────────
user = require_login()
if not user:
    st.stop()

# ── load chat history from Supabase on first visit ─────────────────────────
# Only loads once per session (when chat_messages is still empty).
# After that, new messages are appended locally for speed.
if not st.session_state["chat_messages"]:
    with st.spinner("Loading conversation history..."):
        result = get_chat_history(user["email"])
        if "history" in result:
            st.session_state["chat_messages"] = result["history"]

# ── display all messages ───────────────────────────────────────────────────
# st.chat_message() renders the correct bubble style for "user" vs "assistant"
for msg in st.session_state["chat_messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["message"])

# ── show suggested prompts if conversation is empty ───────────────────────
if not st.session_state["chat_messages"]:
    st.markdown("**Try asking:**")
    suggestions = [
        "What should I eat for breakfast to support my goal?",
        "How much protein do I need daily?",
        "Give me a healthy snack idea under 200 calories.",
        "Explain the difference between good and bad carbs.",
    ]
    cols = st.columns(2)
    for i, suggestion in enumerate(suggestions):
        if cols[i % 2].button(suggestion, use_container_width=True):
            # clicking a suggestion fills the input and sends it
            st.session_state["pending_message"] = suggestion
            st.rerun()

# ── handle a suggestion click that was set in the previous rerun ──────────
if "pending_message" in st.session_state:
    pending = st.session_state.pop("pending_message")
    with st.chat_message("user"):
        st.markdown(pending)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = send_chat_message(user["email"], pending)

    if "error" in result:
        show_error(result["error"])
    else:
        reply = result["reply"]
        with st.chat_message("assistant"):
            st.markdown(reply)

        st.session_state["chat_messages"].append({"role": "user",      "message": pending})
        st.session_state["chat_messages"].append({"role": "assistant", "message": reply})
        st.rerun()

# ── main chat input at the bottom ─────────────────────────────────────────
# st.chat_input() stays pinned at the bottom of the page automatically
if prompt := st.chat_input("Ask me anything about nutrition..."):
    # immediately display the user's message
    with st.chat_message("user"):
        st.markdown(prompt)

    # call Flask and stream the reply
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = send_chat_message(user["email"], prompt)

        if "error" in result:
            show_error(result["error"])
        else:
            reply = result["reply"]
            st.markdown(reply)

            # add both messages to local session state
            st.session_state["chat_messages"].append({"role": "user",      "message": prompt})
            st.session_state["chat_messages"].append({"role": "assistant", "message": reply})