from nutrition_analyzer import analyze_nutrient


result = analyze_nutrient(
    value=10,
    reference_value=25,
    unit="g"
)

print(result)