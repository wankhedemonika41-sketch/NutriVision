import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.services.auth_service import (
    burn_time, clear_failures, create_token, hash_password, read_token,
    record_failure, seconds_until_allowed, verify_password,
)

router = APIRouter(prefix="/auth", tags=["Auth"])

_bearer = HTTPBearer(auto_error=False)
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ------------------------------------------------------------------
# Request / response models
# ------------------------------------------------------------------

def _clean_email(value):
    value = value.strip().lower()
    if len(value) > 254 or not _EMAIL.match(value):
        raise ValueError("Enter a valid email address.")
    return value


class RegisterIn(BaseModel):
    name: str
    email: str
    password: str

    @field_validator("name")
    @classmethod
    def check_name(cls, value):
        value = " ".join(value.split())
        if not 2 <= len(value) <= 60:
            raise ValueError("Name must be 2 to 60 characters.")
        return value

    @field_validator("email")
    @classmethod
    def check_email(cls, value):
        return _clean_email(value)

    @field_validator("password")
    @classmethod
    def check_password(cls, value):
        if not 8 <= len(value) <= 128:
            raise ValueError("Password must be 8 to 128 characters.")
        if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
            raise ValueError("Password must contain at least one letter and one number.")
        return value


class LoginIn(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def check_email(cls, value):
        return value.strip().lower()


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    diet_preference: Optional[str] = None
    allergies: Optional[str] = None
    health_goal: Optional[str] = None


def _session(user):
    return {"token": create_token(user.id), "user": UserOut.model_validate(user)}


# ------------------------------------------------------------------
# "Who is logged in?" - reuse this in any route that needs a user:
#       user: User = Depends(get_current_user)
# ------------------------------------------------------------------

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(get_db),
):
    unauthorised = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Please log in to continue.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorised

    user_id = read_token(credentials.credentials)
    if user_id is None:
        raise unauthorised

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise unauthorised

    return user


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    taken = HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="An account with this email already exists. Please log in.")

    if db.query(User).filter(User.email == body.email).first():
        raise taken

    user = User(
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password),
    )
    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise taken

    db.refresh(user)
    return _session(user)


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    wait = seconds_until_allowed(body.email)
    if wait:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed attempts. Try again in {wait} seconds.",
        )

    user = db.query(User).filter(User.email == body.email).first()

    if user is None:
        burn_time(body.password)
        ok = False
    else:
        ok = verify_password(body.password, user.password_hash)

    if not ok:
        record_failure(body.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.")

    clear_failures(body.email)
    return _session(user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user