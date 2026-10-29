"""
Turns the raw text that OCR read from a food label into
 - an ingredients string
 - a nutrition dict (same field names as the database)

OCR is never perfect, so this module is forgiving and returns warnings
that the user interface shows before anything is analysed.
"""

import re

try:                                   # optional spelling correction
    from rapidfuzz import fuzz, process
except Exception:                      # pragma: no cover
    fuzz = process = None

NUTRIENT_FIELDS = [
    "calories", "carbohydrates", "protein", "total_fat", "saturated_fat",
    "trans_fat", "sugar", "sodium", "fiber", "cholesterol",
]

# ------------------------------------------------------------------
# Ingredients
# ------------------------------------------------------------------

_HEADING = re.compile(r"ingre[dc][il1]ent[s5]?\s*[:;\-\u2013]?", re.I)

_STOP = re.compile(
    r"nutrition(?:al)?\b|allergen|contains\b|may\s+contain|best\s+before|"
    r"use\s+by|\bmfd\b|manufactur|marketed|packed\s+(?:by|on)|"
    r"net\s*(?:wt|weight|quantity|qty)|storage|store\s+in|fssai|\bmrp\b|"
    r"customer\s+care|directions|\bbatch\b|approx\.?\s+values|per\s*100",
    re.I,
)

VOCAB = [
    "sugar", "emulsifier", "emulsifiers", "preservative", "flavour",
    "flavouring", "flavor", "colour", "colours", "color", "wheat", "flour",
    "maida", "refined", "palm", "edible", "vegetable", "oil", "iodised",
    "starch", "maltodextrin", "dextrose", "lecithin", "soya", "milk",
    "solids", "cocoa", "butter", "hydrogenated", "antioxidant", "acidity",
    "regulator", "raising", "agent", "agents", "stabiliser", "stabilizer",
    "sweetener", "aspartame", "sucralose", "tartrazine", "caramel",
    "permitted", "natural", "identical", "artificial", "substances",
    "spices", "condiments", "turmeric", "chilli", "onion", "garlic",
    "invert", "syrup", "glucose", "fructose", "whey", "powder", "yeast",
    "rice", "corn", "maize", "gram", "lentil", "peanut", "almond",
    "cashew", "salt", "water", "acid", "citric", "sodium", "bicarbonate",
    "ammonium", "thickener", "vitamin", "minerals", "protein", "wholegrain",
]
_VOCAB_SET = set(VOCAB)


def _case_like(original, replacement):
    if original.isupper():
        return replacement.upper()
    if original[:1].isupper():
        return replacement.capitalize()
    return replacement


def correct_spelling(text):
    """Fix common OCR slips (e.g. 'emulsifler') using a small food vocabulary."""
    if process is None or not text:
        return text

    def fix(match):
        word = match.group(0)
        lower = word.lower()
        if len(lower) < 6 or lower in _VOCAB_SET:
            return word
        best = process.extractOne(
            lower, VOCAB, scorer=fuzz.ratio, score_cutoff=88)
        if best and best[0][0] == lower[0] and abs(len(best[0]) - len(lower)) <= 1:
            return _case_like(word, best[0])
        return word

    return re.sub(r"[A-Za-z]+", fix, text)


def extract_ingredients(text):
    match = _HEADING.search(text)
    if not match:
        return None

    after = text[match.end():]
    stop = _STOP.search(after)
    chunk = after[:stop.start()] if stop else after[:1500]

    chunk = re.sub(r"(?<=[A-Za-z])-\s*\n\s*(?=[a-z])", "", chunk)   # hyphen splits
    chunk = chunk.replace("|", " ").replace("_", " ")
    chunk = re.sub(r"\s+", " ", chunk).strip(" :;-.,")

    if len(chunk) < 8:
        return None

    return correct_spelling(chunk)


# ------------------------------------------------------------------
# Nutrition
# ------------------------------------------------------------------

# first matching rule wins, so order matters
_ROWS = [
    ("skip",          r"calcium|iron|vitamin|potassium|magnesium|zinc|phosph|"
                      r"mono|poly|mufa|pufa"),
    ("saturated_fat", r"saturat|\bsat\.?\s*fat"),
    ("trans_fat",     r"\btrans"),
    ("cholesterol",   r"cholest"),
    ("added_sugar",   r"added\s+sugar"),
    ("sugar",         r"sugar"),
    ("carbohydrates", r"carbohydrate|carbs?\b"),
    ("fiber",         r"fib(?:re|er)"),
    ("protein",       r"protein"),
    ("total_fat",     r"\bfat\b|total\s+fat"),
    ("sodium",        r"sodium"),
    ("salt",          r"\bsalt\b"),
    ("calories",      r"energy|calori|kcal"),
]
_ROW_RULES = [(name, re.compile(rx, re.I)) for name, rx in _ROWS]

_NUMBER = re.compile(
    r"(?P<num>\d{1,3},\d{3}(?!\d)|\d{1,5}(?:[.,]\d{1,3})?)\s*"
    r"(?P<unit>kcal|kj|mg|mcg|\u00b5g|ug|gm|g|ml)?(?![A-Za-z0-9])",
    re.I,
)

_MG_FIELDS = {"sodium", "cholesterol"}


def _fix_digits(s):
    s = re.sub(r"(?<=\d)[Oo]|[Oo](?=\d)", "0", s)
    s = re.sub(r"(?<=\d)[lI](?=\d)", "1", s)
    return s


def _to_float(raw):
    if re.fullmatch(r"\d{1,3},\d{3}", raw):
        return float(raw.replace(",", ""))
    return float(raw.replace(",", "."))


def _numbers(tail):
    """[(value, unit)] from text, ignoring percentages (RDA columns)."""
    found = []
    for m in _NUMBER.finditer(_fix_digits(tail)):
        after = tail[m.end():m.end() + 3].lstrip()
        if after.startswith("%"):
            continue
        found.append((_to_float(m.group("num")), (m.group("unit") or "").lower()))
    return found


def _basis(text):
    t = text.lower()
    m100 = re.search(r"(?:per|/)\s*100\s*(?:g|gm|ml)\b", t)
    mserv = re.search(r"per\s*(?:serving|serve|portion)", t)

    serving_g = None
    ms = (re.search(r"serv(?:ing|e)\s*size\D{0,12}(\d+(?:[.,]\d+)?)\s*(?:g|gm|ml)", t)
          or re.search(r"per\s*serv(?:ing|e)\D{0,6}(\d+(?:[.,]\d+)?)\s*(?:g|gm|ml)", t))
    if ms:
        serving_g = float(ms.group(1).replace(",", "."))

    if m100 and mserv:
        return "100g", (0 if m100.start() < mserv.start() else 1), serving_g, None
    if m100:
        return "100g", 0, serving_g, None
    if mserv:
        return "serving", 0, serving_g, None
    return "100g", 0, serving_g, (
        "Could not find a 'per 100 g' or 'per serving' heading, so the values "
        "are assumed to be per 100 g. Please check."
    )


def _convert(field, value, unit, line):
    """Bring a value to the unit used in the database (g, mg, kcal)."""
    if not unit:
        hint = re.search(r"\((mg|g|kcal|kj)\)", line, re.I)
        unit = hint.group(1).lower() if hint else ""

    if field in _MG_FIELDS:
        return value * 1000 if unit == "g" else value
    if unit == "mg":
        return value / 1000
    return value


def extract_nutrition(text):
    basis, col, serving_g, basis_warning = _basis(text)

    values = {f: None for f in NUTRIENT_FIELDS}
    salt_g = None
    added_sugar = None

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        field = None
        key_end = 0
        for name, rule in _ROW_RULES:
            m = rule.search(line)
            if m:
                field, key_end = name, m.end()
                break

        if field is None or field == "skip":
            continue

        nums = _numbers(line[key_end:])
        if not nums:
            continue

        # energy: prefer the number written with kcal
        if field == "calories":
            kcal = [v for v, u in nums if u == "kcal"]
            if kcal:
                value = kcal[min(col, len(kcal) - 1)]
            else:
                pick = nums[col] if len(nums) > col else nums[0]
                value = pick[0]
                is_kj = pick[1] == "kj" or (
                    "kj" in line.lower() and "kcal" not in line.lower())
                if is_kj:
                    value = value / 4.184
            if values["calories"] is None:
                values["calories"] = round(value, 1)
            continue

        value, unit = nums[col] if len(nums) > col else nums[0]
        value = _convert(field, value, unit, line)

        if field == "salt":
            salt_g = salt_g if salt_g is not None else value
        elif field == "added_sugar":
            added_sugar = value
        elif values[field] is None:
            values[field] = round(value, 2)

    if values["sodium"] is None and salt_g is not None:
        values["sodium"] = round(salt_g * 400, 1)       # g salt -> mg sodium
    if values["sugar"] is None and added_sugar is not None:
        values["sugar"] = round(added_sugar, 2)

    return values, basis, serving_g, basis_warning


def _check(values):
    warnings = []
    v = values

    found = sum(1 for x in v.values() if x is not None)
    if found < 4:
        warnings.append(
            f"Only {found} nutrition value(s) could be read. "
            "Please fill in the missing ones.")

    if v["calories"] is not None and v["calories"] > 900:
        warnings.append("Calories look too high for 100 g. Check the number.")

    macro = sum(x for x in (v["carbohydrates"], v["protein"], v["total_fat"]) if x)
    if macro > 105:
        warnings.append(
            "Carbohydrate + protein + fat add up to more than 100 g. "
            "Check the numbers (or the 'per serving' / 'per 100 g' column).")

    if v["sugar"] is not None and v["carbohydrates"] is not None \
            and v["sugar"] > v["carbohydrates"] + 0.5:
        warnings.append("Sugar is higher than total carbohydrate. Check both.")

    if v["saturated_fat"] is not None and v["total_fat"] is not None \
            and v["saturated_fat"] > v["total_fat"] + 0.5:
        warnings.append("Saturated fat is higher than total fat. Check both.")

    for field in ("calories", "sugar", "sodium"):
        if v[field] is None:
            warnings.append(f"'{field}' is missing. It is needed for the health score.")

    return warnings


def parse_label(text):
    text = text or ""
    ingredients = extract_ingredients(text)
    nutrition, basis, serving_g, basis_warning = extract_nutrition(text)

    warnings = _check(nutrition)
    if basis_warning:
        warnings.insert(0, basis_warning)
    if ingredients is None:
        warnings.append("Could not find the ingredients list.")

    return {
        "ingredients": ingredients,
        "nutrition": nutrition,
        "basis": basis,
        "serving_size_g": serving_g,
        "found_fields": [k for k, v in nutrition.items() if v is not None],
        "warnings": warnings,
    }