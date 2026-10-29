"""
OCR for food-label photos.

Engines (tried in this order unless OCR_ENGINE is set):
  1. Tesseract  (pytesseract + the Tesseract program installed on the PC)
  2. EasyOCR    (pip install easyocr, needs PyTorch, bigger but no extra program)

Set OCR_ENGINE=tesseract or OCR_ENGINE=easyocr to force one.
Set TESSERACT_CMD to the full path of tesseract.exe if it is not found.
"""

import os
import shutil
from functools import lru_cache

import cv2
import numpy as np


class OCRUnavailable(RuntimeError):
    """No OCR engine could be started."""


WINDOWS_TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# ------------------------------------------------------------------
# Image preparation
# ------------------------------------------------------------------

def decode_image(data):
    array = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("The file is not a readable image.")
    return image


def _resize(image, low=1600, high=3000):
    h, w = image.shape[:2]
    longest = max(h, w)
    if longest < low:
        scale, method = low / longest, cv2.INTER_CUBIC
    elif longest > high:
        scale, method = high / longest, cv2.INTER_AREA
    else:
        return image
    return cv2.resize(image, None, fx=scale, fy=scale, interpolation=method)


def _deskew(gray):
    """Straighten a tilted photo (tries -10..+10 degrees)."""
    small_scale = 800 / max(gray.shape[:2])
    small = cv2.resize(gray, None, fx=small_scale, fy=small_scale,
                       interpolation=cv2.INTER_AREA) if small_scale < 1 else gray
    _, binary = cv2.threshold(small, 0, 255,
                              cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    h, w = binary.shape
    centre = (w / 2, h / 2)

    def sharpness(angle):
        matrix = cv2.getRotationMatrix2D(centre, angle, 1.0)
        rotated = cv2.warpAffine(binary, matrix, (w, h))
        return float(np.var(rotated.sum(axis=1)))

    best = max(np.arange(-10, 10.5, 1.0), key=sharpness)
    best = max(np.arange(best - 0.8, best + 0.9, 0.2), key=sharpness)

    if abs(best) < 0.5:
        return gray

    gh, gw = gray.shape[:2]
    matrix = cv2.getRotationMatrix2D((gw / 2, gh / 2), best, 1.0)
    return cv2.warpAffine(gray, matrix, (gw, gh),
                          flags=cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_REPLICATE)


def preprocess(image):
    """Straightened photo as grayscale and as black-and-white."""
    image = _resize(image)
    gray = _deskew(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY))
    gray = cv2.fastNlMeansDenoising(gray, None, 8, 7, 21)
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 15)
    return [gray, binary]


# ------------------------------------------------------------------
# Tesseract
# ------------------------------------------------------------------

def _tesseract_ready():
    try:
        import pytesseract
    except Exception:
        return None

    command = os.getenv("TESSERACT_CMD")
    if command and os.path.exists(command):
        pytesseract.pytesseract.tesseract_cmd = command
    elif shutil.which("tesseract"):
        pass
    elif os.path.exists(WINDOWS_TESSERACT):
        pytesseract.pytesseract.tesseract_cmd = WINDOWS_TESSERACT
    else:
        return None

    try:
        pytesseract.get_tesseract_version()
    except Exception:
        return None
    return pytesseract


def _run_tesseract(pytesseract, image):
    data = pytesseract.image_to_data(
        image, lang="eng", config="--oem 3 --psm 6",
        output_type=pytesseract.Output.DICT)

    lines, confidences = {}, []
    for i, word in enumerate(data["text"]):
        word = word.strip()
        try:
            conf = float(data["conf"][i])
        except (TypeError, ValueError):
            continue
        if not word or conf < 0:
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        lines.setdefault(key, []).append(word)
        confidences.append(conf)

    text = "\n".join(" ".join(words) for _, words in sorted(lines.items()))
    good = sum(c for c in confidences if c >= 50)
    mean = sum(confidences) / len(confidences) if confidences else 0.0
    return text, round(mean, 1), len(confidences), good


# ------------------------------------------------------------------
# EasyOCR
# ------------------------------------------------------------------

@lru_cache(maxsize=1)
def _easyocr_reader():
    try:
        import easyocr
    except Exception:
        return None
    try:
        return easyocr.Reader(["en"], gpu=False, verbose=False)
    except Exception:
        return None


def _group_lines(items):
    """items: [(x, y_centre, height, text, conf)] -> text lines."""
    items = sorted(items, key=lambda it: it[1])
    rows, current, last_y = [], [], None
    for item in items:
        if last_y is not None and abs(item[1] - last_y) > item[2] * 0.6:
            rows.append(current)
            current = []
        current.append(item)
        last_y = item[1]
    if current:
        rows.append(current)
    return "\n".join(
        " ".join(it[3] for it in sorted(row, key=lambda it: it[0]))
        for row in rows)


def _run_easyocr(reader, image):
    results = reader.readtext(image, detail=1, paragraph=False)
    items, confidences = [], []
    for box, text, conf in results:
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        items.append((min(xs), sum(ys) / len(ys), max(ys) - min(ys), text, conf))
        confidences.append(conf * 100)
    text = _group_lines(items)
    good = sum(c for c in confidences if c >= 50)
    mean = sum(confidences) / len(confidences) if confidences else 0.0
    return text, round(mean, 1), len(confidences), good


# ------------------------------------------------------------------
# Public function
# ------------------------------------------------------------------

def available_engines():
    engines = []
    if _tesseract_ready() is not None:
        engines.append("tesseract")
    try:
        import easyocr  # noqa: F401
        engines.append("easyocr")
    except Exception:
        pass
    return engines


def run_ocr(data):
    """Image bytes -> {"engine", "text", "confidence", "words"}."""
    wanted = os.getenv("OCR_ENGINE", "auto").lower()
    image = decode_image(data)
    height, width = image.shape[:2]

    runner = None
    engine = None

    if wanted in ("auto", "tesseract"):
        tess = _tesseract_ready()
        if tess is not None:
            engine, runner = "tesseract", lambda img: _run_tesseract(tess, img)

    if runner is None and wanted in ("auto", "easyocr"):
        reader = _easyocr_reader()
        if reader is not None:
            engine, runner = "easyocr", lambda img: _run_easyocr(reader, img)

    if runner is None:
        raise OCRUnavailable(
            "No OCR engine is available. Install Tesseract "
            "(https://github.com/UB-Mannheim/tesseract/wiki) and run "
            "'pip install pytesseract', or run 'pip install easyocr'.")

    best = None
    for variant in preprocess(image):
        text, confidence, words, good = runner(variant)
        if best is None or good > best[3]:
            best = (text, confidence, words, good)

    text, confidence, words, _ = best
    return {
        "engine": engine, "text": text, "confidence": confidence,
        "words": words, "width": width, "height": height,
    }