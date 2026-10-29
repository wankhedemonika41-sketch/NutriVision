from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.analysis.ingredient_analyzer import ALLERGENS
from app.database.connection import get_db
from app.models.user import User
from app.routes.auth_routes import get_current_user
from app.services.profile_service import (
    DIET_VALUES, DIETS, GENDER_VALUES, GENDERS, GOAL_VALUES, GOALS, compute_bmi,
)

router = APIRouter(prefix="/profile", tags=["Profile"])

ALLERGEN_NAMES = list(ALLERGENS.keys())


def _in_range(value, low, high, label):
    if value is not None and not low <= value <= high:
        raise ValueError(f"{label} must be between {low:g} and {high:g}.")
    return value


def _one_of(value, allowed, label):
    if value is not None and value not in allowed:
        raise ValueError(f"Unknown {label}.")
    return value


class ProfileIn(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    diet_preference: Optional[str] = None
    allergies: List[str] = []
    health_goal: Optional[str] = None

    @field_validator("age")
    @classmethod
    def check_age(cls, v):
        return _in_range(v, 5, 120, "Age")

    @field_validator("height_cm")
    @classmethod
    def check_height(cls, v):
        return _in_range(v, 50, 250, "Height (cm)")

    @field_validator("weight_kg")
    @classmethod
    def check_weight(cls, v):
        return _in_range(v, 10, 300, "Weight (kg)")

    @field_validator("gender")
    @classmethod
    def check_gender(cls, v):
        return _one_of(v, GENDER_VALUES, "gender")

    @field_validator("diet_preference")
    @classmethod
    def check_diet(cls, v):
        return _one_of(v, DIET_VALUES, "diet preference")

    @field_validator("health_goal")
    @classmethod
    def check_goal(cls, v):
        return _one_of(v, GOAL_VALUES, "health goal")

    @field_validator("allergies")
    @classmethod
    def check_allergies(cls, values):
        clean = []
        for name in values:
            if name not in ALLERGEN_NAMES:
                raise ValueError(f"Unknown allergen: {name}.")
            if name not in clean:
                clean.append(name)
        return clean


def allergy_list(user):
    return [a for a in (user.allergies or "").split(",") if a]


def _profile_out(user):
    return {
        "profile": {
            "age": user.age,
            "gender": user.gender,
            "height_cm": user.height_cm,
            "weight_kg": user.weight_kg,
            "diet_preference": user.diet_preference,
            "allergies": allergy_list(user),
            "health_goal": user.health_goal,
        },
        "bmi": compute_bmi(user.height_cm, user.weight_kg, user.age),
    }


@router.get("/options")
def options():
    """Choices for the profile form (kept on the server so they never drift)."""
    return {
        "allergens": ALLERGEN_NAMES,
        "diets": [{"value": v, "label": l} for v, l in DIETS],
        "goals": [{"value": v, "label": l} for v, l in GOALS],
        "genders": [{"value": v, "label": l} for v, l in GENDERS],
    }


@router.get("")
def get_profile(user: User = Depends(get_current_user)):
    return _profile_out(user)


@router.put("")
def save_profile(
    body: ProfileIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Replaces the whole profile with what the form sends."""
    user.age = body.age
    user.gender = body.gender
    user.height_cm = body.height_cm
    user.weight_kg = body.weight_kg
    user.diet_preference = body.diet_preference
    user.allergies = ",".join(body.allergies) or None
    user.health_goal = body.health_goal

    db.add(user)
    db.commit()
    db.refresh(user)

    return _profile_out(user)