from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.connection import engine
from app.database.base import Base


# ============================================================
# MODELS
# ============================================================

from app.models.product import Product
from app.models.nutrition import Nutrition
from app.models.ingredient import Ingredient
from app.models.reference_value import ReferenceValue


# ============================================================
# ROUTES
# ============================================================

from app.routes.product_routes import router as product_router
from app.routes.nutrition_routes import router as nutrition_router
from app.routes.ingredient_routes import router as ingredient_router
from app.routes.reference_value_routes import (
    router as reference_value_router
)


# ============================================================
# NUTRITION ANALYSIS ROUTE
# ============================================================

from app.routes.nutrition_analysis_routes import (
    router as nutrition_analysis_router
)


# ============================================================
# OPEN FOOD FACTS ROUTE
# ============================================================

from app.routes.open_food_facts_routes import (
    router as open_food_facts_router
)


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# CREATE FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="NutriVision API",
    description="Smart Food Label and Ingredient Analysis System",
    version="1.0.0"
)


# ============================================================
# CORS CONFIGURATION
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REGISTER ROUTES
# ============================================================

app.include_router(product_router)

app.include_router(nutrition_router)

app.include_router(ingredient_router)

app.include_router(reference_value_router)


# ============================================================
# REGISTER NUTRITION ANALYSIS API
# ============================================================

app.include_router(nutrition_analysis_router)


# ============================================================
# REGISTER OPEN FOOD FACTS API
# ============================================================

app.include_router(open_food_facts_router)


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def root():

    return {
        "message": "Welcome to NutriVision API",
        "status": "running"
    }


# ============================================================
# DATABASE CONNECTION TEST
# ============================================================

@app.get("/database-test")
def database_test():

    try:

        with engine.connect():

            return {
                "database": "connected",
                "status": "success"
            }

    except Exception as e:

        return {
            "database": "connection failed",
            "error": str(e)
        }