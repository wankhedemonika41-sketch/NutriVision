from sqlalchemy import Column, Integer, String, Float

from app.database.base import Base


class ReferenceValue(Base):
    __tablename__ = "reference_values"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    nutrient = Column(
        String(100),
        nullable=False,
        unique=True
    )

    reference_value = Column(
        Float,
        nullable=False
    )

    unit = Column(
        String(20),
        nullable=False
    )

    basis = Column(
        String(100),
        nullable=False
    )

    description = Column(
        String(500),
        nullable=True
    )