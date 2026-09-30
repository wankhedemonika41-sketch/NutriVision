def calculate_percentage(value, reference_value):
    """
    Calculate how much of the selected reference value
    is contributed by one serving of the product.
    """

    if value is None or reference_value is None:
        return None

    if reference_value <= 0:
        return None

    percentage = (value / reference_value) * 100

    return round(percentage, 2)


def classify_nutrient(percentage):
    """
    Classify the nutritional contribution.

    These are project-defined analytical categories.
    They are NOT medical diagnoses.
    """

    if percentage is None:
        return "UNKNOWN"

    if percentage < 20:
        return "LOW"

    elif percentage < 40:
        return "MODERATE"

    else:
        return "HIGH"


def analyze_nutrient(value, reference_value, unit):
    """
    Perform percentage calculation and classification
    for a single nutrient.
    """

    percentage = calculate_percentage(
        value,
        reference_value
    )

    level = classify_nutrient(
        percentage
    )

    return {
        "value": value,
        "reference_value": reference_value,
        "unit": unit,
        "percentage": percentage,
        "level": level
    }