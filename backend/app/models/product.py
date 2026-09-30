from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from datetime import datetime
from sqlalchemy.orm import relationship

from app.database.base import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    product_name = Column(String(200), nullable=False)

    brand = Column(String(150), nullable=True)

    category = Column(String(100), nullable=True)

    sub_category = Column(String(150), nullable=True)

    barcode = Column(String(50), unique=True, nullable=True)

    serving_size = Column(String(100), nullable=True)

    ingredients = Column(Text, nullable=True)

    price_inr = Column(Float, nullable=True)

    source_of_data = Column(String(200), nullable=True)

    collection_date = Column(String(50), nullable=True)

    collected_by = Column(String(150), nullable=True)

    remarks = Column(Text, nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    nutrition = relationship(
        "Nutrition",
        back_populates="product",
        uselist=False,
        cascade="all, delete-orphan"
    )

    ingredient_list = relationship(
        "Ingredient",
        back_populates="product",
        cascade="all, delete-orphan"
    )