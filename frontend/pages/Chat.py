import os
import sys

import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from frontend.components.api_client import get_chat_history, send_chat_message
from frontend.components.ui_helpers import apply_theme, require_login, show_card, show_error


st.set_page_config(page_title="Chat - NutriAI", page_icon="💬")

apply_theme(
    "Chat with NutriAI",
    "Ask for food swaps, healthy snacks, meal ideas, or nutrition help in a friendlier conversation space.",
    badge="Chat Lounge",
)
show_card("Conversation ideas", "Try breakfast ideas, protein questions, snack swaps, hydration tips, or anything related to your nutrition goals.")

user = require_login()
if not user:
    st.stop()

if not st.session_state["chat_messages"]:
    with st.spinner("Loading conversation history..."):
        result = get_chat_history(user["email"])
        if "history" in result:
            st.session_state["chat_messages"] = result["history"]

for msg in st.session_state["chat_messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["message"])

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
            st.session_state["pending_message"] = suggestion
            st.rerun()

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

        st.session_state["chat_messages"].append({"role": "user", "message": pending})
        st.session_state["chat_messages"].append({"role": "assistant", "message": reply})
        st.rerun()

if prompt := st.chat_input("Ask me anything about nutrition..."):
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = send_chat_message(user["email"], prompt)

        if "error" in result:
            show_error(result["error"])
        else:
            reply = result["reply"]
            st.markdown(reply)
            st.session_state["chat_messages"].append({"role": "user", "message": prompt})
            st.session_state["chat_messages"].append({"role": "assistant", "message": reply})
