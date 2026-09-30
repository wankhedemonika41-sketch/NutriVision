from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models.product import Product
from app.schemas.product_schema import (
    ProductCreate,
    ProductResponse,
    ProductDetailsResponse
)


router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ============================================================
# CREATE PRODUCT
# ============================================================

@router.post("/", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db)
):

    new_product = Product(
        product_name=product.product_name,
        brand=product.brand,
        category=product.category,
        sub_category=product.sub_category,
        barcode=product.barcode,
        serving_size=product.serving_size,
        ingredients=product.ingredients,
        price_inr=product.price_inr,
        source_of_data=product.source_of_data,
        collection_date=product.collection_date,
        collected_by=product.collected_by,
        remarks=product.remarks
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product


# ============================================================
# GET ALL PRODUCTS
# ============================================================

@router.get("/", response_model=list[ProductResponse])
def get_products(
    db: Session = Depends(get_db)
):

    return db.query(Product).all()


# ============================================================
# SEARCH PRODUCTS
# ============================================================

@router.get(
    "/search",
    response_model=list[ProductResponse]
)
def search_products(
    q: str = Query(
        ...,
        min_length=1,
        description="Product name to search for"
    ),
    db: Session = Depends(get_db)
):

    products = db.query(Product).filter(
        Product.product_name.ilike(f"%{q}%")
    ).all()

    return products


# ============================================================
# GET PRODUCT DETAILS
# ============================================================

@router.get(
    "/details/{product_id}",
    response_model=ProductDetailsResponse
)
def get_product_details(
    product_id: int,
    db: Session = Depends(get_db)
):

    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if product is None:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return {
        "product": product,
        "nutrition": product.nutrition
    }


# ============================================================
# GET PRODUCT BY BARCODE
# ============================================================

@router.get(
    "/barcode/{barcode}",
    response_model=ProductResponse
)
def get_product_by_barcode(
    barcode: str,
    db: Session = Depends(get_db)
):

    product = db.query(Product).filter(
        Product.barcode == barcode
    ).first()

    if product is None:

        raise HTTPException(
            status_code=404,
            detail="Product not found for this barcode"
        )

    return product


# ============================================================
# GET PRODUCT BY ID
# ============================================================

@router.get(
    "/{product_id}",
    response_model=ProductResponse
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):

    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if product is None:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return product