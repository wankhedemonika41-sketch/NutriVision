from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, field_validator, model_validator
from sqlalchemy.orm import Session, joinedload

from app.analysis.ingredient_analyzer import analyze_ingredients
from app.database.connection import get_db
from app.models.product import Product
from app.models.scan_history import ScanHistory
from app.models.user import User
from app.routes.auth_routes import get_current_user
from app.schemas.product_schema import ProductResponse
from app.services.health_score_service import compute_health
from app.services.history_service import split_cautions, summarize, to_utc

router = APIRouter(prefix="/history", tags=["History"])

MAX_ENTRIES = 1000          # per user; the oldest ones are dropped beyond this
DUPLICATE_MINUTES = 10      # opening the same product again within this time is not logged twice

NUTRITION_FIELDS = [
    "calories", "carbohydrates", "protein", "total_fat", "saturated_fat",
    "trans_fat", "sugar", "sodium", "fiber", "cholesterol",
]


class HistoryIn(BaseModel):
    source: Literal["product", "barcode", "label"]

    # source == "product": only the id is needed, the server works the rest out
    product_id: Optional[int] = None

    # source == "barcode" / "label": a snapshot of the result the user saw
    barcode: Optional[str] = None
    product_name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    score: Optional[float] = None
    grade: Optional[Literal["A", "B", "C", "D"]] = None
    calories: Optional[float] = None
    sugar: Optional[float] = None
    sodium: Optional[float] = None
    saturated_fat: Optional[float] = None
    protein: Optional[float] = None
    fiber: Optional[float] = None
    cautions: List[str] = []

    @field_validator("product_id")
    @classmethod
    def check_product_id(cls, v):
        if v is not None and v < 1:
            raise ValueError("Invalid product id.")
        return v

    @field_validator("barcode")
    @classmethod
    def check_barcode(cls, v):
        if v is not None and not (v.isdigit() and 6 <= len(v) <= 14):
            raise ValueError("A barcode contains 6 to 14 digits.")
        return v

    @field_validator("product_name", "brand", "category")
    @classmethod
    def clean_text(cls, v):
        if v is None:
            return None
        v = " ".join(v.split())
        return v[:200] or None

    @field_validator("score")
    @classmethod
    def check_score(cls, v):
        if v is not None and not 0 <= v <= 100:
            raise ValueError("Score must be between 0 and 100.")
        return v

    @field_validator("calories", "sugar", "sodium", "saturated_fat", "protein", "fiber")
    @classmethod
    def check_nutrient(cls, v):
        if v is not None and not 0 <= v <= 100000:
            raise ValueError("Nutrient values must be positive numbers.")
        return v

    @field_validator("cautions")
    @classmethod
    def check_cautions(cls, values):
        clean = []
        for value in values:
            value = " ".join(value.replace(",", " ").split())[:40]
            if value and value not in clean:
                clean.append(value)
        return clean[:8]

    @model_validator(mode="after")
    def check_source(self):
        if self.source == "product":
            if self.product_id is None:
                raise ValueError("product_id is required for source 'product'.")
        elif not (self.product_name and self.score is not None and self.grade):
            raise ValueError("product_name, score and grade are required.")
        return self


def _entry_out(row):
    return {
        "id": row.id,
        "created_at": to_utc(row.created_at).isoformat(),
        "source": row.source,
        "product_id": row.product_id,
        "barcode": row.barcode,
        "product_name": row.product_name,
        "brand": row.brand,
        "category": row.category,
        "score": row.score,
        "grade": row.grade,
        "cautions": split_cautions(row.cautions),
    }


def _snapshot_for_product(db, product_id):
    """The server works out the score itself, so a stored 'product' entry is trustworthy."""
    product = (
        db.query(Product)
        .options(joinedload(Product.nutrition))
        .filter(Product.id == product_id)
        .first()
    )

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found.")

    if product.nutrition is None:
        raise HTTPException(status_code=422, detail="This product has no nutrition data.")

    nutrition = {f: getattr(product.nutrition, f, None) for f in NUTRITION_FIELDS}
    data = ProductResponse.model_validate(product).model_dump()
    health = compute_health(data, nutrition, explain=False)

    if not health or not health.get("available"):
        raise HTTPException(status_code=422, detail="No health score could be calculated.")

    per100 = health["per_100g"]
    highlights = analyze_ingredients(data.get("ingredients"))["highlights"]

    return {
        "product_id": product.id,
        "product_name": (data.get("product_name") or "Unnamed product")[:200],
        "brand": data.get("brand"),
        "category": data.get("category"),
        "score": health["score"],
        "grade": health["grade"],
        "calories": per100.get("calories"),
        "sugar": per100.get("sugar"),
        "sodium": per100.get("sodium"),
        "saturated_fat": per100.get("saturated_fat"),
        "protein": per100.get("protein"),
        "fiber": per100.get("fiber"),
        "cautions": [h["label"] for h in highlights if h["severity"] == "caution"][:8],
    }


@router.post("")
def record(
    body: HistoryIn,
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.source == "product":
        data = _snapshot_for_product(db, body.product_id)
        same = ScanHistory.product_id == body.product_id
    else:
        data = body.model_dump(exclude={"source", "product_id"})
        data["product_id"] = None
        same = ScanHistory.barcode == body.barcode if body.barcode else None

    now = datetime.now(timezone.utc)

    if same is not None:
        recent = (
            db.query(ScanHistory)
            .filter(ScanHistory.user_id == user.id, same,
                    ScanHistory.created_at >= now - timedelta(minutes=DUPLICATE_MINUTES))
            .first()
        )
        if recent is not None:
            return {"id": recent.id, "duplicate": True}

    cautions = data.pop("cautions", [])
    row = ScanHistory(
        user_id=user.id, source=body.source, created_at=now,
        cautions=",".join(cautions) or None, **data)
    db.add(row)
    db.commit()

    # keep each user's history to a sensible size
    extra = db.query(ScanHistory).filter(ScanHistory.user_id == user.id).count() - MAX_ENTRIES
    if extra > 0:
        oldest = (
            db.query(ScanHistory.id).filter(ScanHistory.user_id == user.id)
            .order_by(ScanHistory.created_at.asc(), ScanHistory.id.asc())
            .limit(extra).all()
        )
        db.query(ScanHistory).filter(ScanHistory.id.in_([i for (i,) in oldest])).delete(
            synchronize_session=False)
        db.commit()

    response.status_code = status.HTTP_201_CREATED
    return {"id": row.id, "duplicate": False}


@router.get("")
def list_history(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(ScanHistory).filter(ScanHistory.user_id == user.id)
    rows = (
        query.order_by(ScanHistory.created_at.desc(), ScanHistory.id.desc())
        .offset(offset).limit(limit).all()
    )
    return {"total": query.count(), "items": [_entry_out(r) for r in rows]}


@router.get("/summary")
def history_summary(
    days: int = Query(7, ge=1, le=365),
    tz_offset: int = Query(0, ge=-840, le=840, description="Minutes the user's clock is ahead of UTC"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)

    rows = (
        db.query(ScanHistory)
        .filter(ScanHistory.user_id == user.id,
                ScanHistory.created_at >= now - timedelta(days=2 * days + 2))
        .all()
    )

    entries = [{
        "created_at": r.created_at, "score": r.score, "grade": r.grade,
        "category": r.category, "product_name": r.product_name,
        "product_id": r.product_id, "barcode": r.barcode,
        "cautions": split_cautions(r.cautions),
        "calories": r.calories, "sugar": r.sugar, "sodium": r.sodium,
        "saturated_fat": r.saturated_fat,
    } for r in rows]

    return summarize(entries, days, now, tz_offset)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(
    entry_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(ScanHistory)
        .filter(ScanHistory.id == entry_id, ScanHistory.user_id == user.id)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="History entry not found.")

    db.delete(row)
    db.commit()


@router.delete("")
def clear_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deleted = db.query(ScanHistory).filter(ScanHistory.user_id == user.id).delete(
        synchronize_session=False)
    db.commit()
    return {"deleted": deleted}