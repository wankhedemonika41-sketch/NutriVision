from sqlalchemy import Column, Integer, Float, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database.base import Base


class Nutrition(Base):
    __tablename__ = "nutrition"

    id = Column(Integer, primary_key=True, index=True)

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False
    )

    calories = Column(Float, nullable=True)

    carbohydrates = Column(Float, nullable=True)

    protein = Column(Float, nullable=True)

    total_fat = Column(Float, nullable=True)

    saturated_fat = Column(Float, nullable=True)

    trans_fat = Column(Float, nullable=True)

    sugar = Column(Float, nullable=True)

    sodium = Column(Float, nullable=True)

    fiber = Column(Float, nullable=True)

    cholesterol = Column(Float, nullable=True)

    calcium = Column(Float, nullable=True)

    vitamin = Column(String(200), nullable=True)

    iron = Column(Float, nullable=True)

    product = relationship(
        "Product",
        back_populates="nutrition"
    )