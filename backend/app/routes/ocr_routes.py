from typing import Dict, Literal, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.analysis.ingredient_analyzer import analyze_ingredients
from app.services.health_score_service import compute_health
from app.services.label_parser import NUTRIENT_FIELDS, parse_label
from app.services.ocr_service import OCRUnavailable, available_engines, run_ocr

router = APIRouter(prefix="/ocr", tags=["OCR"])

MAX_IMAGE_BYTES = 8 * 1024 * 1024


@router.get("/status")
def ocr_status():
    """Which OCR engines work on this computer."""
    engines = available_engines()
    return {"ready": bool(engines), "engines": engines}


@router.post("/scan")
def scan_label(file: UploadFile = File(...)):
    """Photo of a label -> text read by OCR + parsed ingredients/nutrition."""
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file.")

    data = file.file.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image is larger than 8 MB.")

    try:
        ocr = run_ocr(data)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except OCRUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error))

    parsed = parse_label(ocr["text"])

    if ocr["confidence"] < 60:
        parsed["warnings"].insert(
            0, "The photo is hard to read. Try a closer, straighter, "
               "better-lit photo of the label.")
    
    
    if max(ocr["width"], ocr["height"]) < 1000:
        parsed["warnings"].insert(
            0, f"This image is only {ocr['width']} x {ocr['height']} pixels, "
               "which is too small to read label text. Use a photo that is at "
               "least 1500 pixels on its long side, or crop it to just the "
               "nutrition table.")

    

    return {
        "engine": ocr["engine"],
        "confidence": ocr["confidence"],
        "raw_text": ocr["text"],
        **parsed,
    }


class LabelInput(BaseModel):
    product_name: Optional[str] = None
    category: Optional[str] = None
    ingredients: Optional[str] = None
    nutrition: Dict[str, Optional[float]]
    basis: Literal["100g", "serving"] = "100g"
    serving_size_g: Optional[float] = None


@router.post("/analyze")
def analyze_label(body: LabelInput):
    """Values the user has checked/edited -> health score + ingredient analysis."""
    nutrition = {}
    for field in NUTRIENT_FIELDS:
        value = body.nutrition.get(field)
        if value is not None and not 0 <= value <= 100000:
            raise HTTPException(
                status_code=422, detail=f"'{field}' must be a positive number.")
        nutrition[field] = value

    if body.basis == "serving":
        if not body.serving_size_g or body.serving_size_g <= 0:
            raise HTTPException(
                status_code=422,
                detail="Enter the serving size (in g) to convert 'per serving' values.")
        factor = 100.0 / body.serving_size_g
        nutrition = {
            k: (None if v is None else round(v * factor, 2))
            for k, v in nutrition.items()
        }

    product = {
        "product_name": (body.product_name or "").strip() or "Scanned label",
        "brand": None,
        "category": body.category,
        "ingredients": body.ingredients,
        "serving_size": None,
        "image_url": None,
    }

    health = compute_health(product, nutrition, already_per_100g=True)

    return {
        "source": "Label photo (OCR)",
        "product": product,
        "nutrition": nutrition,
        "ingredient_analysis": analyze_ingredients(body.ingredients),
        "health": health,
    }