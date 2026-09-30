from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database.base import Base


class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False
    )

    name = Column(
        String(200),
        nullable=False
    )

    category = Column(
        String(100),
        nullable=True
    )

    explanation = Column(
        String(500),
        nullable=True
    )

    product = relationship(
        "Product",
        back_populates="ingredient_list"
    )