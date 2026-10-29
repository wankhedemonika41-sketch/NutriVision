from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String

from app.database.base import Base


def _now():
    return datetime.now(timezone.utc)


class ScanHistory(Base):
    """One product a user looked at (opened, scanned or read from a label)."""

    __tablename__ = "scan_history"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), default=_now, nullable=False, index=True)

    source = Column(String(10), nullable=False)          # product | barcode | label

    product_id = Column(Integer, nullable=True)          # only for products in our database
    barcode = Column(String(20), nullable=True)

    product_name = Column(String(200), nullable=False)
    brand = Column(String(120), nullable=True)
    category = Column(String(80), nullable=True)

    score = Column(Float, nullable=False)
    grade = Column(String(2), nullable=False)

    # per 100 g, kept so reports can show averages later
    calories = Column(Float, nullable=True)
    sugar = Column(Float, nullable=True)
    sodium = Column(Float, nullable=True)
    saturated_fat = Column(Float, nullable=True)
    protein = Column(Float, nullable=True)
    fiber = Column(Float, nullable=True)

    cautions = Column(String(255), nullable=True)        # "Added sugar,Palm oil"