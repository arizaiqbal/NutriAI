import numpy as np


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    """
    Calculates Body Mass Index using NumPy.
    Formula: BMI = weight (kg) / height (m)^2
    
    Args:
        weight_kg: user's weight in kilograms
        height_cm: user's height in centimetres
    
    Returns:
        BMI value rounded to 2 decimal places
    """
    height_m = np.array(height_cm) / 100        # convert cm to metres
    bmi = np.array(weight_kg) / (height_m ** 2) # core BMI formula
    return round(float(bmi), 2)


def get_bmi_category(bmi: float) -> str:
    """
    Returns the WHO BMI category label for a given BMI value.
    """
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25.0:
        return "Normal weight"
    elif bmi < 30.0:
        return "Overweight"
    else:
        return "Obese"


def calculate_daily_calories(
    weight_kg: float,
    height_cm: float,
    age: int,
    gender: str,
    goal: str,
    activity_level: str = "moderate"
) -> int:
    """
    Calculates daily calorie target using the Mifflin-St Jeor BMR formula
    adjusted by an activity multiplier, then modified for the user's goal.

    Formula:
        Male   BMR = (10 * weight) + (6.25 * height) - (5 * age) + 5
        Female BMR = (10 * weight) + (6.25 * height) - (5 * age) - 161
    
    Activity multipliers:
        sedentary  → 1.2   (little or no exercise)
        light      → 1.375 (light exercise 1-3 days/week)
        moderate   → 1.55  (moderate exercise 3-5 days/week)
        active     → 1.725 (hard exercise 6-7 days/week)
    
    Goal adjustment:
        loss        → TDEE - 500  (0.5 kg/week deficit)
        gain        → TDEE + 300  (slow lean gain)
        maintenance → TDEE (no change)

    Args:
        weight_kg:      weight in kg
        height_cm:      height in cm
        age:            age in years
        gender:         "male" or "female"
        goal:           "loss", "gain", or "maintenance"
        activity_level: "sedentary", "light", "moderate", or "active"
    
    Returns:
        Daily calorie target as an integer
    """
    # Step 1: calculate BMR using NumPy arrays for precision
    w = np.array(weight_kg, dtype=float)
    h = np.array(height_cm, dtype=float)
    a = np.array(age,       dtype=float)

    if gender.lower() == "male":
        bmr = (10 * w) + (6.25 * h) - (5 * a) + 5
    else:
        bmr = (10 * w) + (6.25 * h) - (5 * a) - 161

    # Step 2: apply activity multiplier to get TDEE
    multipliers = {
        "sedentary": 1.2,
        "light":     1.375,
        "moderate":  1.55,
        "active":    1.725
    }
    tdee = bmr * multipliers.get(activity_level, 1.55)

    # Step 3: adjust for goal
    if goal == "loss":
        target = tdee - 500
    elif goal == "gain":
        target = tdee + 300
    else:
        target = tdee

    return int(target)


def get_macro_targets(daily_calories: int, goal: str) -> dict:
    """
    Returns recommended daily macronutrient targets in grams
    based on calorie goal.
    
    Protein/carb/fat split:
        loss        → 40% protein, 30% carbs, 30% fat
        gain        → 25% protein, 50% carbs, 25% fat
        maintenance → 30% protein, 40% carbs, 30% fat

    Calories per gram: protein=4, carbs=4, fat=9
    """
    splits = {
        "loss":        {"protein": 0.40, "carbs": 0.30, "fat": 0.30},
        "gain":        {"protein": 0.25, "carbs": 0.50, "fat": 0.25},
        "maintenance": {"protein": 0.30, "carbs": 0.40, "fat": 0.30},
    }
    s = splits.get(goal, splits["maintenance"])

    return {
        "protein_g": int((daily_calories * s["protein"]) / 4),
        "carbs_g":   int((daily_calories * s["carbs"])   / 4),
        "fat_g":     int((daily_calories * s["fat"])     / 9),
    }