from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models.reference_value import ReferenceValue
from app.schemas.reference_value_schema import (
    ReferenceValueCreate,
    ReferenceValueResponse
)


router = APIRouter(
    prefix="/reference-values",
    tags=["Reference Values"]
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post(
    "/",
    response_model=ReferenceValueResponse
)
def create_reference_value(
    reference: ReferenceValueCreate,
    db: Session = Depends(get_db)
):

    existing = db.query(ReferenceValue).filter(
        ReferenceValue.nutrient == reference.nutrient
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Reference value already exists"
        )

    new_reference = ReferenceValue(
        nutrient=reference.nutrient,
        daily_value=reference.daily_value,
        unit=reference.unit
    )

    db.add(new_reference)
    db.commit()
    db.refresh(new_reference)

    return new_reference


@router.get(
    "/",
    response_model=list[ReferenceValueResponse]
)
def get_reference_values(
    db: Session = Depends(get_db)
):

    return db.query(ReferenceValue).all()


@router.get(
    "/{reference_id}",
    response_model=ReferenceValueResponse
)
def get_reference_value(
    reference_id: int,
    db: Session = Depends(get_db)
):

    reference = db.query(ReferenceValue).filter(
        ReferenceValue.id == reference_id
    ).first()

    if reference is None:
        raise HTTPException(
            status_code=404,
            detail="Reference value not found"
        )

    return reference