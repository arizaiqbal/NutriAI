from groq import Groq
from backend.config import GROQ_API_KEY, GROQ_MODEL

# Create the client once at module level — reused across all calls
client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
You are NutriAI, a professional nutrition and diet assistant.
You help users with:
- Personalized meal planning based on their BMI, calorie targets, and dietary goals
- Nutrition advice and macronutrient explanations
- Healthy recipe suggestions using available ingredients
- Grocery list recommendations
- General healthy eating guidance

Always be encouraging, practical, and specific. When giving meal suggestions,
include approximate calories and macros. Keep responses concise and friendly.
Never give medical diagnoses — always recommend consulting a doctor for health conditions.
"""


def ask_groq(user_message: str, chat_history: list = None) -> str:
    """
    Sends a message to Groq's LLM and returns the reply text.

    Args:
        user_message:  the latest message from the user
        chat_history:  list of previous messages in format
                       [{"role": "user", "message": "..."}, ...]
                       This gives the LLM memory of the conversation.

    Returns:
        The assistant's reply as a plain string.

    How the messages list is built:
        1. System prompt first — sets the AI's persona and rules
        2. Previous messages from chat_history — gives conversation context
        3. Current user message last
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # add conversation history so Groq remembers earlier messages
    if chat_history:
        for entry in chat_history:
            messages.append({
                "role":    entry["role"],      # "user" or "assistant"
                "content": entry["message"]
            })

    # add the current message
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model       = GROQ_MODEL,
        messages    = messages,
        max_tokens  = 1024,
        temperature = 0.7,  # 0=deterministic, 1=creative — 0.7 balances both
    )

    return response.choices[0].message.content


def ask_groq_with_context(user_message: str, user_profile: dict, chat_history: list = None) -> str:
    """
    Same as ask_groq but injects the user's health profile into
    the system prompt so every reply is personalized.

    For example, Groq will know the user's calorie target and goal
    without the user having to repeat it in every message.
    """
    personalized_system = SYSTEM_PROMPT + f"""

Current user profile:
- Name: {user_profile.get('name', 'User')}
- Goal: {user_profile.get('goal', 'maintenance')}
- Daily calorie target: {user_profile.get('daily_calories', 'unknown')} kcal
- BMI: {user_profile.get('bmi', 'unknown')} ({user_profile.get('bmi_category', '')})
- Dietary restrictions: {user_profile.get('restrictions', 'none')}
- Daily macro targets: {user_profile.get('protein_g', '?')}g protein, 
  {user_profile.get('carbs_g', '?')}g carbs, {user_profile.get('fat_g', '?')}g fat

Always tailor your advice to this user's specific profile.
"""
    messages = [{"role": "system", "content": personalized_system}]

    if chat_history:
        for entry in chat_history:
            messages.append({"role": entry["role"], "content": entry["message"]})

    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model       = GROQ_MODEL,
        messages    = messages,
        max_tokens  = 1024,
        temperature = 0.7,
    )

    return response.choices[0].message.content
