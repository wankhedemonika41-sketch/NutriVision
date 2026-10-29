from sqlalchemy.orm import Session

from app.analysis.reference_defaults import DEFAULT_REFERENCE_VALUES
from app.models.reference_value import ReferenceValue


def seed_reference_values(db: Session) -> int:
    """Insert any missing default reference values. Safe to run repeatedly."""

    existing = {
        row.nutrient.lower()
        for row in db.query(ReferenceValue.nutrient).all()
    }

    added = 0

    for item in DEFAULT_REFERENCE_VALUES:
        if item["nutrient"] in existing:
            continue

        db.add(ReferenceValue(**item))
        added += 1

    if added:
        db.commit()

    return added
