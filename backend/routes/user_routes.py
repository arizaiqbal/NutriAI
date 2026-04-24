from flask import Blueprint, request, jsonify
from backend.services.bmi_service import calculate_bmi, calculate_daily_calories, get_bmi_category, get_macro_targets
from backend.services.notification_service import get_water_reminder
from backend.services.supabase_service import save_user, get_user_by_email, update_user

# Blueprint object — "user" is its internal name, used for url_for() lookups
user_bp = Blueprint("user", __name__)


@user_bp.route("/register", methods=["POST"])
def register():
    """
    Registers a new user.

    Expects JSON body:
    {
        "email":        "ariza@nu.edu.pk",
        "name":         "Ariza",
        "height_cm":    165,
        "weight_kg":    58,
        "age":          20,
        "gender":       "female",
        "goal":         "maintenance",
        "restrictions": "none",
        "activity_level": "moderate"
    }

    What happens inside:
    1. Extract data from the request body
    2. Validate that required fields are present
    3. Calculate BMI and daily calorie target using bmi_service
    4. Build the full user dict and save it to Supabase
    5. Return the saved user data as JSON
    """
    data = request.get_json()

    # --- validation ---
    required = ["email", "name", "height_cm", "weight_kg", "age", "gender", "goal"]
    missing = [field for field in required if field not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    # --- calculations ---
    bmi = calculate_bmi(data["weight_kg"], data["height_cm"])
    daily_calories = calculate_daily_calories(
        weight_kg      = data["weight_kg"],
        height_cm      = data["height_cm"],
        age            = data["age"],
        gender         = data["gender"],
        goal           = data["goal"],
        activity_level = data.get("activity_level", "moderate")
    )
    bmi_category = get_bmi_category(bmi)
    macros = get_macro_targets(daily_calories, data["goal"])

    # --- build user record ---
    user_record = {
        "email":          data["email"],
        "name":           data["name"],
        "height_cm":      data["height_cm"],
        "weight_kg":      data["weight_kg"],
        "age":            data["age"],
        "gender":         data["gender"],
        "goal":           data["goal"],
        "restrictions":   data.get("restrictions", "none"),
        "daily_calories": daily_calories,
        "bmi":            bmi,
        "bmi_category":   bmi_category,
        "protein_g":      macros["protein_g"],
        "carbs_g":        macros["carbs_g"],
        "fat_g":          macros["fat_g"],
    }

    saved = save_user(user_record)
    if not saved:
        return jsonify({"error": "Failed to save user profile"}), 500

    return jsonify({
        "message": "User registered successfully",
        "user": saved,
        "notification": get_water_reminder(saved.get("name", "")),
    }), 201


@user_bp.route("/profile", methods=["GET"])
def get_profile():
    """
    Fetches a user's profile by email.

    Expects query parameter: ?email=ariza@nu.edu.pk
    Usage from Streamlit: requests.get("http://localhost:5000/api/user/profile?email=...")
    
    Returns the full user dict or a 404 if not found.
    """
    email = request.args.get("email")
    if not email:
        return jsonify({"error": "email query parameter is required"}), 400

    user = get_user_by_email(email)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "user": user,
        "notification": get_water_reminder(user.get("name", "")),
    }), 200


@user_bp.route("/update", methods=["PUT"])
def update_profile():
    """
    Updates a user's profile and recalculates BMI/calories if
    weight, height, or goal has changed.

    Expects JSON body:
    {
        "email":      "ariza@nu.edu.pk",
        "weight_kg":  60,        ← optional, only fields being updated
        "goal":       "loss"     ← optional
    }
    """
    data = request.get_json()
    email = data.get("email")
    if not email:
        return jsonify({"error": "email is required"}), 400

    # fetch current profile to fill in any missing values needed for recalc
    current = get_user_by_email(email)
    if not current:
        return jsonify({"error": "User not found"}), 404

    # merge: use new value if provided, else keep existing
    weight_kg = data.get("weight_kg",   current["weight_kg"])
    height_cm = data.get("height_cm",   current["height_cm"])
    age       = data.get("age",         current["age"])
    gender    = data.get("gender",      current["gender"])
    goal      = data.get("goal",        current["goal"])
    activity  = data.get("activity_level", "moderate")

    # recalculate
    bmi            = calculate_bmi(weight_kg, height_cm)
    daily_calories = calculate_daily_calories(weight_kg, height_cm, age, gender, goal, activity)
    macros         = get_macro_targets(daily_calories, goal)

    updates = {
        **data,  # include whatever fields the user sent
        "bmi":            bmi,
        "bmi_category":   get_bmi_category(bmi),
        "daily_calories": daily_calories,
        "protein_g":      macros["protein_g"],
        "carbs_g":        macros["carbs_g"],
        "fat_g":          macros["fat_g"],
    }
    updates.pop("email", None)  # don't update the email column itself

    updated = update_user(email, updates)
    return jsonify({"message": "Profile updated", "user": updated}), 200
