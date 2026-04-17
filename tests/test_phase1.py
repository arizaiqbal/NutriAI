"""
Phase 1 tests — run with: python -m pytest tests/test_phase1.py -v
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.bmi_service import (
    calculate_bmi,
    get_bmi_category,
    calculate_daily_calories,
    get_macro_targets,
)


# ─── BMI TESTS ───────────────────────────────────────────────────────────────

def test_bmi_normal():
    bmi = calculate_bmi(weight_kg=70, height_cm=175)
    assert bmi == 22.86, f"Expected 22.86, got {bmi}"

def test_bmi_underweight():
    bmi = calculate_bmi(weight_kg=45, height_cm=170)
    assert get_bmi_category(bmi) == "Underweight"

def test_bmi_overweight():
    bmi = calculate_bmi(weight_kg=75, height_cm=170)
    assert get_bmi_category(bmi) == "Overweight"

def test_bmi_obese():
    bmi = calculate_bmi(weight_kg=120, height_cm=170)
    assert get_bmi_category(bmi) == "Obese"


# ─── CALORIE TESTS ───────────────────────────────────────────────────────────

def test_calories_male_maintenance():
    cal = calculate_daily_calories(70, 175, 25, "male", "maintenance")
    assert 2500 < cal < 2800, f"Unexpected value: {cal}"

def test_calories_female_loss():
    cal = calculate_daily_calories(60, 165, 22, "female", "loss")
    assert 1400 < cal < 1700, f"Unexpected value: {cal}"

def test_calories_male_gain():
    cal_maint = calculate_daily_calories(70, 175, 25, "male", "maintenance")
    cal_gain  = calculate_daily_calories(70, 175, 25, "male", "gain")
    assert cal_gain > cal_maint, "Gain calories should be higher than maintenance"

def test_calories_loss_lower_than_maintenance():
    cal_maint = calculate_daily_calories(70, 175, 25, "female", "maintenance")
    cal_loss  = calculate_daily_calories(70, 175, 25, "female", "loss")
    assert cal_loss < cal_maint


# ─── MACRO TESTS ─────────────────────────────────────────────────────────────

def test_macros_add_up_approximately():
    macros = get_macro_targets(2000, "maintenance")
    # recalculate calories from grams: protein*4 + carbs*4 + fat*9
    reconstructed = (macros["protein_g"] * 4 +
                     macros["carbs_g"]   * 4 +
                     macros["fat_g"]     * 9)
    # allow ±50 cal rounding tolerance
    assert abs(reconstructed - 2000) < 50, f"Macros don't add up: {reconstructed}"

def test_macros_loss_high_protein():
    macros_loss = get_macro_targets(2000, "loss")
    macros_gain = get_macro_targets(2000, "gain")
    assert macros_loss["protein_g"] > macros_gain["protein_g"], \
        "Loss plan should have more protein than gain plan"


# ─── CONFIG TEST ─────────────────────────────────────────────────────────────

def test_config_loads():
    from backend.config import SUPABASE_URL, SUPABASE_KEY
    assert SUPABASE_URL is not None, ".env SUPABASE_URL not loaded"
    assert SUPABASE_KEY is not None, ".env SUPABASE_KEY not loaded"


if __name__ == "__main__":
    # run manually without pytest
    test_bmi_normal()
    test_bmi_underweight()
    test_bmi_overweight()
    test_bmi_obese()
    test_calories_male_maintenance()
    test_calories_female_loss()
    test_calories_male_gain()
    test_calories_loss_lower_than_maintenance()
    test_macros_add_up_approximately()
    test_macros_loss_high_protein()
    test_config_loads()
    print("All Phase 1 tests passed.")