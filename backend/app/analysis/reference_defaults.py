"""
Default daily reference values used for "% of daily value".

These are approximate adult reference values for a 2000 kcal diet
(FDA Daily Values; WHO limits for free sugars and sodium).
They are stored in the reference_values table so they can be edited
without changing code.
"""

DEFAULT_REFERENCE_VALUES = [
    {"nutrient": "calories", "reference_value": 2000, "unit": "kcal",
     "basis": "per day (2000 kcal diet)",
     "description": "Typical adult daily energy reference."},
    {"nutrient": "protein", "reference_value": 50, "unit": "g",
     "basis": "per day (2000 kcal diet)",
     "description": "Daily reference intake for protein."},
    {"nutrient": "carbohydrates", "reference_value": 275, "unit": "g",
     "basis": "per day (2000 kcal diet)",
     "description": "Daily reference intake for carbohydrates."},
    {"nutrient": "total_fat", "reference_value": 78, "unit": "g",
     "basis": "per day (2000 kcal diet)",
     "description": "Daily reference value for total fat."},
    {"nutrient": "saturated_fat", "reference_value": 20, "unit": "g",
     "basis": "per day (2000 kcal diet)",
     "description": "Daily limit for saturated fat."},
    {"nutrient": "sugar", "reference_value": 50, "unit": "g",
     "basis": "per day",
     "description": "WHO upper limit for free sugars (about 10% of energy)."},
    {"nutrient": "sodium", "reference_value": 2000, "unit": "mg",
     "basis": "per day",
     "description": "WHO recommended maximum sodium intake (about 5 g salt)."},
    {"nutrient": "fiber", "reference_value": 28, "unit": "g",
     "basis": "per day (2000 kcal diet)",
     "description": "Daily reference intake for dietary fibre."},
    {"nutrient": "cholesterol", "reference_value": 300, "unit": "mg",
     "basis": "per day",
     "description": "Daily limit for cholesterol."},
    {"nutrient": "calcium", "reference_value": 1300, "unit": "mg",
     "basis": "per day",
     "description": "Daily reference intake for calcium."},
    {"nutrient": "iron", "reference_value": 18, "unit": "mg",
     "basis": "per day",
     "description": "Daily reference intake for iron."},
]
