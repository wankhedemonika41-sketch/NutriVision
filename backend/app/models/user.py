from sqlalchemy import Column, DateTime, Float, Integer, String, func

from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(60), nullable=False)

    email = Column(String(254), nullable=False, unique=True, index=True)

    password_hash = Column(String(255), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Profile (filled in later from the Profile page; used for recommendations)
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    diet_preference = Column(String(30), nullable=True)
    allergies = Column(String(255), nullable=True)
    health_goal = Column(String(40), nullable=True)