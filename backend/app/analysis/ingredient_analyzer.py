"""
Ingredient analysis.

1. Splits the ingredient text into separate ingredients
   (commas inside brackets do not split).
2. Flags ingredients that are worth knowing about
   (palm oil, added sugars, additives, ...).
3. Detects common allergens from the text.

This is rule based and works only on the written ingredient list.
It is general information, not medical advice.
"""

import re

# (id, label, severity, regex, note)
# severity: "caution" (worth limiting), "info" (good to know), "positive"
RULES = [
    ("palm_oil", "Palm oil", "caution",
     r"palm\s*-?(oil|olein|kernel)|palmolein",
     "Palm oil is high in saturated fat."),

    ("added_sugar", "Added sugar", "caution",
     r"\b(sugar|invert sugar|glucose|liquid glucose|fructose|dextrose|"
     r"maltodextrin|corn syrup|jaggery|honey|syrup)\b",
     "A form of added sugar."),

    ("refined_flour", "Refined flour", "info",
     r"refined wheat flour|\bmaida\b|refined flour",
     "Refined flour has less fibre than whole grain."),

    ("whole_grain", "Whole grain", "positive",
     r"whole wheat|\batta\b|whole grain|wholegrain|\boats?\b|millet|"
     r"\bragi\b|jowar|bajra",
     "Whole grains add fibre."),

    ("hydrogenated", "Hydrogenated fat", "caution",
     r"hydrogenated|vanaspati|margarine|shortening|interesterified",
     "Processed fats like this can contain trans fat."),

    ("synthetic_colour", "Synthetic colour", "caution",
     r"tartrazine|sunset yellow|carmoisine|ponceau|allura|brilliant blue|"
     r"erythrosine|\bINS\s?(102|110|122|129|133|124)\b",
     "Synthetic food colour."),

    ("flavour_enhancer", "Flavour enhancer", "info",
     r"monosodium glutamate|\bmsg\b|\bINS\s?621\b|disodium (inosinate|"
     r"guanylate)|flavou?r enhancer|\b(627|631)\b",
     "Used to boost savoury taste."),

    ("artificial_flavour", "Artificial / nature-identical flavour", "info",
     r"artificial|nature[- ]identical|synthetic",
     "Flavour or colour not taken directly from the natural source."),

    ("sweetener", "Sweetener", "info",
     r"aspartame|sucralose|acesulfame|saccharin|cyclamate|sorbitol|"
     r"maltitol|xylitol|erythritol|stevia",
     "Low-calorie or sugar-alcohol sweetener."),

    ("preservative", "Preservative", "info",
     r"sodium benzoate|potassium sorbate|sorbic acid|benzoic acid|"
     r"sulphite|sulfite|nitrite|propionate|preservative",
     "Used to extend shelf life."),

    ("additive", "Food additive", "info",
     r"emulsifier|raising agent|acidity regulator|antioxidant|"
     r"stabili[sz]er|thickener|gelling agent|anti-?caking|humectant|"
     r"dough conditioner|flour treatment|\b(?:INS|E)[\s-]?\d{3}[a-z]?\b",
     "Additive used for texture, rising, acidity or stability."),
]

ALLERGENS = {
    "Milk": r"\bmilk\b|whey|casein|lactose|cheese|\bghee\b|\bcurd\b|"
            r"paneer|cream(?! of tartar)|(?<!cocoa )(?<!shea )(?<!peanut )butter",
    "Soy": r"\bsoy\b|\bsoya\b|soybean",
    "Wheat / Gluten": r"wheat|\bmaida\b|\batta\b|gluten|semolina|\bsuji\b|"
                      r"\brava\b|barley|\brye\b",
    "Peanut": r"peanut|groundnut",
    "Tree nuts": r"almond|cashew|hazelnut|walnut|pistachio|pecan",
    "Egg": r"\begg",
    "Sesame": r"\bsesame\b",
}

_COMPILED_RULES = [
    (rid, label, severity, re.compile(pattern, re.I), note)
    for rid, label, severity, pattern, note in RULES
]

_COMPILED_ALLERGENS = {
    name: re.compile(pattern, re.I) for name, pattern in ALLERGENS.items()
}


def split_ingredients(text):
    """Split on commas / semicolons that are not inside brackets."""

    if not text:
        return []

    parts, current, depth = [], [], 0

    for ch in text:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth = max(0, depth - 1)

        if ch in ",;" and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)

    parts.append("".join(current))

    cleaned = [re.sub(r"\s+", " ", p).strip(" .*\u00a0") for p in parts]

    return [p for p in cleaned if p]


def _matching_open(text):
    """Index of the '(' / '[' that matches the final ')' / ']' of text."""

    depth = 0
    for index in range(len(text) - 1, -1, -1):
        if text[index] in ")]}":
            depth += 1
        elif text[index] in "([{":
            depth -= 1
            if depth == 0:
                return index
    return -1


def flatten_ingredients(text):
    """
    Split into individual ingredients and expand nested lists, e.g.
    "seasoning (spices, sugar, salt)" -> "seasoning", "spices", "sugar", "salt".
    Brackets that only hold codes or one phrase, such as "(330, 296)" or
    "(soy lecithin)", are kept with their ingredient.
    """

    result = []

    for item in split_ingredients(text):
        if item[-1] in ")]}":
            start = _matching_open(item)
            inner = item[start + 1:-1] if start > 0 else ""
            parent = item[:start].strip() if start > 0 else ""
            parts = split_ingredients(inner)

            if parent and len(parts) > 1 and re.search(r"[A-Za-z]{4,}", inner):
                result.append(parent)
                result.extend(flatten_ingredients(inner))
                continue

        result.append(item)

    return result


def analyze_ingredients(text):
    """Return flags per ingredient, grouped highlights and allergens."""

    ingredients = flatten_ingredients(text)

    if not ingredients:
        return {
            "count": 0,
            "ingredients": [],
            "highlights": [],
            "allergens": [],
            "top_ingredient_notes": [],
            "disclaimer": "Ingredient information is not available.",
        }

    items = []
    grouped = {}

    for position, name in enumerate(ingredients):
        flags = []

        for rid, label, severity, regex, note in _COMPILED_RULES:
            if regex.search(name):
                flags.append(
                    {"type": rid, "label": label,
                     "severity": severity, "note": note}
                )
                group = grouped.setdefault(
                    rid,
                    {"type": rid, "label": label, "severity": severity,
                     "note": note, "ingredients": []},
                )
                group["ingredients"].append(name)

        items.append({"position": position + 1, "name": name, "flags": flags})

    allergens = [
        name for name, regex in _COMPILED_ALLERGENS.items()
        if regex.search(" ".join(ingredients))
    ]

    # Ingredients are listed from largest to smallest amount.
    top_notes = []
    for item in items[:3]:
        for flag in item["flags"]:
            if flag["type"] in ("added_sugar", "palm_oil", "hydrogenated"):
                top_notes.append(
                    f"{flag['label']} appears among the first three "
                    f"ingredients ({item['name']}), so it is one of the "
                    f"main components."
                )

    order = {"caution": 0, "info": 1, "positive": 2}
    highlights = sorted(grouped.values(), key=lambda g: order[g["severity"]])

    return {
        "count": len(items),
        "ingredients": items,
        "highlights": highlights,
        "allergens": allergens,
        "top_ingredient_notes": list(dict.fromkeys(top_notes)),
        "disclaimer": (
            "Based on the written ingredient list only. Always check the "
            "pack for the official allergen statement."
        ),
    }
