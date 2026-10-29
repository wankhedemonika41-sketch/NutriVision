"""Helpers for cleaning the messy packaged-food CSV."""

import re

import pandas as pd


def clean_text(value):
    """Strip spaces / non-breaking spaces. Empty -> None."""

    if value is None or pd.isna(value):
        return None

    text = str(value).replace("\u00a0", " ").replace("\ufeff", "")
    text = re.sub(r"\s+", " ", text).strip()

    return text or None


def clean_name(value):
    """Product names: also remove (R)/(TM) symbols."""

    text = clean_text(value)

    if text is None:
        return None

    text = re.sub(r"[\u00ae\u2122]", "", text)

    return re.sub(r"\s+", " ", text).strip() or None


def parse_number(value):
    """
    Convert messy CSV numbers.

    Returns (number_or_None, note_or_None).

        12.5      -> (12.5, None)
        "7,65"    -> (7.65, None)       decimal comma
        "<1"      -> (0.5, "trace")     "less than x" is estimated as x/2
        "5.928.8" -> (None, "invalid")  cannot be trusted
        empty     -> (None, None)
    """

    if value is None:
        return None, None

    if isinstance(value, (int, float)):
        if pd.isna(value):
            return None, None
        return float(value), None

    text = str(value).strip().replace("\u00a0", "")

    if text == "" or text.lower() in ("nan", "na", "n/a", "-"):
        return None, None

    trace = False

    if text.startswith("<"):
        trace = True
        text = text[1:].strip()

    # decimal comma:  "7,65" -> "7.65"
    if re.fullmatch(r"\d+,\d+", text):
        text = text.replace(",", ".")

    try:
        number = float(text)
    except ValueError:
        return None, "invalid"

    if trace:
        return round(number / 2, 3), "trace"

    return number, None


def format_serving(value):
    """Serving size 100.0 -> '100 g'. Keeps text such as '1 pack'."""

    if value is None or pd.isna(value):
        return None

    try:
        number = float(value)
        return f"{number:g} g"
    except (TypeError, ValueError):
        return clean_text(value)
