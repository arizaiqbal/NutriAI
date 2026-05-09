import numpy as np


_CALORIE_TRAINING_DATA = [
    {"weight": 48, "height": 158, "age": 21, "gender": "female", "activity": "sedentary", "daily_calories": 1550},
    {"weight": 54, "height": 162, "age": 24, "gender": "female", "activity": "light", "daily_calories": 1780},
    {"weight": 60, "height": 165, "age": 22, "gender": "female", "activity": "moderate", "daily_calories": 2010},
    {"weight": 67, "height": 168, "age": 29, "gender": "female", "activity": "active", "daily_calories": 2275},
    {"weight": 72, "height": 170, "age": 35, "gender": "female", "activity": "moderate", "daily_calories": 2120},
    {"weight": 80, "height": 175, "age": 32, "gender": "female", "activity": "active", "daily_calories": 2440},
    {"weight": 62, "height": 170, "age": 23, "gender": "male", "activity": "sedentary", "daily_calories": 1960},
    {"weight": 68, "height": 174, "age": 26, "gender": "male", "activity": "light", "daily_calories": 2235},
    {"weight": 74, "height": 178, "age": 27, "gender": "male", "activity": "moderate", "daily_calories": 2520},
    {"weight": 80, "height": 180, "age": 31, "gender": "male", "activity": "active", "daily_calories": 2830},
    {"weight": 88, "height": 183, "age": 36, "gender": "male", "activity": "moderate", "daily_calories": 2740},
    {"weight": 96, "height": 188, "age": 40, "gender": "male", "activity": "active", "daily_calories": 3090},
]

_MEAL_TRAINING_DATA = [
    {"calories": 320, "protein": 28, "carbs": 26, "fat": 10, "label": "healthy"},
    {"calories": 380, "protein": 30, "carbs": 35, "fat": 11, "label": "healthy"},
    {"calories": 420, "protein": 32, "carbs": 38, "fat": 13, "label": "healthy"},
    {"calories": 450, "protein": 27, "carbs": 40, "fat": 15, "label": "healthy"},
    {"calories": 520, "protein": 34, "carbs": 45, "fat": 16, "label": "healthy"},
    {"calories": 560, "protein": 36, "carbs": 48, "fat": 18, "label": "healthy"},
    {"calories": 430, "protein": 16, "carbs": 52, "fat": 14, "label": "moderate"},
    {"calories": 510, "protein": 18, "carbs": 62, "fat": 18, "label": "moderate"},
    {"calories": 590, "protein": 20, "carbs": 70, "fat": 20, "label": "moderate"},
    {"calories": 640, "protein": 22, "carbs": 74, "fat": 24, "label": "moderate"},
    {"calories": 700, "protein": 19, "carbs": 78, "fat": 28, "label": "moderate"},
    {"calories": 760, "protein": 21, "carbs": 82, "fat": 30, "label": "moderate"},
    {"calories": 780, "protein": 11, "carbs": 92, "fat": 34, "label": "unhealthy"},
    {"calories": 860, "protein": 12, "carbs": 96, "fat": 38, "label": "unhealthy"},
    {"calories": 930, "protein": 14, "carbs": 102, "fat": 42, "label": "unhealthy"},
    {"calories": 1020, "protein": 15, "carbs": 108, "fat": 48, "label": "unhealthy"},
    {"calories": 1100, "protein": 17, "carbs": 116, "fat": 54, "label": "unhealthy"},
    {"calories": 1250, "protein": 18, "carbs": 128, "fat": 62, "label": "unhealthy"},
]

_ACTIVITY_MAP = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

_NUMERIC_ACTIVITY_MAP = {
    # Frontend uses:
    # 1 = Low, 2 = Moderate, 3 = High
    1: 1.2,
    2: 1.55,
    3: 1.725,
    # Keep broader compatibility for callers that still send 4 or 5
    4: 1.9,
    5: 1.9,
}

_CLASS_TO_INDEX = {"unhealthy": 0, "moderate": 1, "healthy": 2}
_INDEX_TO_CLASS = {value: key for key, value in _CLASS_TO_INDEX.items()}
_CLASS_SCORE = {"unhealthy": 20, "moderate": 60, "healthy": 90}


def _normalize_activity_level(activity_level):
    if isinstance(activity_level, str):
        return _ACTIVITY_MAP.get(activity_level.strip().lower(), 1.55)

    try:
        return _NUMERIC_ACTIVITY_MAP.get(int(activity_level), 1.55)
    except (TypeError, ValueError):
        return 1.55


def _gender_to_number(gender):
    return 1.0 if str(gender).strip().lower() == "male" else 0.0


def _build_calorie_regression():
    feature_rows = []
    targets = []

    for row in _CALORIE_TRAINING_DATA:
        feature_rows.append([
            float(row["weight"]),
            float(row["height"]),
            float(row["age"]),
            _gender_to_number(row["gender"]),
            _normalize_activity_level(row["activity"]),
        ])
        targets.append(float(row["daily_calories"]))

    x = np.array(feature_rows, dtype=float)
    y = np.array(targets, dtype=float)
    x_with_bias = np.column_stack([np.ones(len(x)), x])
    coefficients, _, _, _ = np.linalg.lstsq(x_with_bias, y, rcond=None)
    return coefficients


def _build_meal_classifier():
    feature_rows = []
    labels = []

    for row in _MEAL_TRAINING_DATA:
        feature_rows.append([
            float(row["calories"]),
            float(row["protein"]),
            float(row["carbs"]),
            float(row["fat"]),
        ])
        labels.append(_CLASS_TO_INDEX[row["label"]])

    features = np.array(feature_rows, dtype=float)
    means = features.mean(axis=0)
    stds = features.std(axis=0)
    stds[stds == 0] = 1.0
    normalized = (features - means) / stds
    return normalized, np.array(labels, dtype=int), means, stds


_CALORIE_COEFFICIENTS = _build_calorie_regression()
_MEAL_FEATURES, _MEAL_LABELS, _MEAL_MEANS, _MEAL_STDS = _build_meal_classifier()


def predict_calories(weight, height, age, gender, activity_level=2):
    """
    Predict daily calories using a small learned linear regression model
    trained on embedded user-stat nutrition samples.
    """
    features = np.array([
        1.0,
        float(weight),
        float(height),
        float(age),
        _gender_to_number(gender),
        _normalize_activity_level(activity_level),
    ])

    prediction = float(features @ _CALORIE_COEFFICIENTS)
    return max(1200, round(prediction))


def get_health_score(calories, protein, carbs, fat):
    """
    Score a meal with a small k-nearest-neighbors classifier trained on
    embedded nutrition samples labeled as healthy, moderate, or unhealthy.
    """
    sample = np.array([
        float(calories),
        float(protein),
        float(carbs),
        float(fat),
    ], dtype=float)

    normalized_sample = (sample - _MEAL_MEANS) / _MEAL_STDS
    distances = np.linalg.norm(_MEAL_FEATURES - normalized_sample, axis=1)
    nearest_indices = np.argsort(distances)[:5]

    class_weights = {"healthy": 0.0, "moderate": 0.0, "unhealthy": 0.0}
    for idx in nearest_indices:
        label = _INDEX_TO_CLASS[int(_MEAL_LABELS[idx])]
        weight = 1.0 / max(float(distances[idx]), 1e-6)
        class_weights[label] += weight

    total_weight = sum(class_weights.values()) or 1.0
    weighted_score = sum(
        (_CLASS_SCORE[label] * weight) for label, weight in class_weights.items()
    ) / total_weight

    return max(0, min(100, round(weighted_score)))


def get_model_info():
    return {
        "model_name": "embedded-nutrition-ml-suite",
        "version": "2.0",
        "type": "linear-regression + k-nearest-neighbors",
        "calorie_training_samples": len(_CALORIE_TRAINING_DATA),
        "health_training_samples": len(_MEAL_TRAINING_DATA),
    }
