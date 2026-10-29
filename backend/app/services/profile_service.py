"""Profile options and BMI."""

DIETS = [
    ("no_preference", "No preference"),
    ("vegetarian", "Vegetarian"),
    ("eggetarian", "Eggetarian (vegetarian + egg)"),
    ("vegan", "Vegan"),
    ("non_vegetarian", "Non-vegetarian"),
]

GOALS = [
    ("general", "General healthy eating"),
    ("lose_weight", "Lose weight"),
    ("manage_sugar", "Manage sugar intake"),
    ("heart_health", "Heart health (less fat and salt)"),
    ("build_muscle", "Build muscle (more protein)"),
]

GENDERS = [
    ("female", "Female"),
    ("male", "Male"),
    ("other", "Other"),
    ("prefer_not_to_say", "Prefer not to say"),
]

DIET_VALUES = [value for value, _ in DIETS]
GOAL_VALUES = [value for value, _ in GOALS]
GENDER_VALUES = [value for value, _ in GENDERS]


def compute_bmi(height_cm, weight_kg, age=None):
    """
    BMI with the Asian-Indian cut-offs (overweight from 23, obese from 25).
    A screening number only, not a diagnosis. For people under 18 the adult
    categories do not apply, so no category is given.
    """
    if not height_cm or not weight_kg:
        return {
            "value": None,
            "category": None,
            "note": "Add your height and weight to see your BMI.",
        }

    value = round(weight_kg / (height_cm / 100) ** 2, 1)

    if age is not None and age < 18:
        return {
            "value": value,
            "category": None,
            "note": ("BMI categories for children and teenagers need "
                     "age-specific growth charts, so none is shown."),
        }

    if value < 18.5:
        category = "Underweight"
    elif value < 23:
        category = "Healthy weight"
    elif value < 25:
        category = "Overweight"
    else:
        category = "Obese"

    return {
        "value": value,
        "category": category,
        "note": ("Uses Asian-Indian cut-offs (overweight from 23, obese from "
                 "25). BMI is a screening number, not a diagnosis."),
    }