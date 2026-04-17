from flask import Blueprint, request, jsonify
from backend.services.groq_service import ask_groq_with_context
from backend.services.supabase_service import (
    get_user_by_email,
    get_chat_history,
    save_chat_message
)

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/message", methods=["POST"])
def send_message():
    """
    Receives a user's chat message, sends it to Groq with context,
    saves both sides of the conversation, and returns the reply.

    Expects JSON body:
    {
        "email":   "ariza@nu.edu.pk",
        "message": "What should I eat for breakfast?"
    }

    What happens step by step:
    1. Get user email + message from request
    2. Load user profile from Supabase (for personalization)
    3. Load recent chat history from Supabase (for conversation memory)
    4. Send message + profile + history to Groq
    5. Save user message to Supabase
    6. Save Groq's reply to Supabase
    7. Return the reply to Streamlit
    """
    data = request.get_json()
    email   = data.get("email")
    message = data.get("message")

    if not email or not message:
        return jsonify({"error": "email and message are required"}), 400

    # step 2: load user profile
    user = get_user_by_email(email)
    if not user:
        return jsonify({"error": "User not found. Please register first."}), 404

    # step 3: load last 10 messages for conversation memory
    history = get_chat_history(user["id"], limit=10)

    # step 4: call Groq
    reply = ask_groq_with_context(
        user_message = message,
        user_profile = user,
        chat_history = history
    )

    # step 5 & 6: persist both messages to Supabase
    save_chat_message(user["id"], role="user",      message=message)
    save_chat_message(user["id"], role="assistant", message=reply)

    return jsonify({"reply": reply}), 200


@chat_bp.route("/history", methods=["GET"])
def get_history():
    """
    Returns chat history for a user.
    Useful for re-loading the chat when the user reopens the app.

    Expects query parameter: ?email=ariza@nu.edu.pk
    """
    email = request.args.get("email")
    if not email:
        return jsonify({"error": "email is required"}), 400

    user = get_user_by_email(email)
    if not user:
        return jsonify({"error": "User not found"}), 404

    history = get_chat_history(user["id"], limit=50)
    return jsonify({"history": history}), 200