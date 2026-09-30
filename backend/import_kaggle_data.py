import sys
import os

import pandas as pd
from sqlalchemy.orm import Session

# Add backend folder to Python path
sys.path.append(
    os.path.dirname(os.path.abspath(__file__))
)

from app.database.connection import SessionLocal

# Import all models so SQLAlchemy knows about relationships
from app.models.product import Product
from app.models.nutrition import Nutrition
from app.models.ingredient import Ingredient
from app.models.reference_value import ReferenceValue


# ============================================================
# CSV FILE LOCATION
# ============================================================

CSV_FILE = os.path.join(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    ),
    "packaged_foods_india.csv"
)


# ============================================================
# CLEAN NUMBER
# ============================================================

def clean_number(value):
    """
    Convert a value into a number.

    Empty or invalid values become None.
    """

    if pd.isna(value):
        return None

    try:
        return float(value)

    except (ValueError, TypeError):
        return None


# ============================================================
# CLEAN TEXT
# ============================================================

def clean_text(value):
    """
    Convert a value into clean text.

    Empty values become None.
    """

    if pd.isna(value):
        return None

    value = str(value).strip()

    if value == "":
        return None

    return value


# ============================================================
# IMPORT DATA
# ============================================================

def import_data():

    print("Starting NutriVision dataset import...")
    print()

    # --------------------------------------------------------
    # Check CSV file
    # --------------------------------------------------------

    if not os.path.exists(CSV_FILE):

        print("CSV file not found:")
        print(CSV_FILE)

        return

    # --------------------------------------------------------
    # Read CSV
    # --------------------------------------------------------

    try:

        df = pd.read_csv(CSV_FILE)

    except Exception as e:

        print("Could not read CSV file.")
        print()
        print("Error:")
        print(e)

        return

    print("CSV loaded successfully.")
    print(f"Total records found: {len(df)}")
    print()

    # --------------------------------------------------------
    # Create database session
    # --------------------------------------------------------

    db: Session = SessionLocal()

    inserted_products = 0
    inserted_nutrition = 0
    skipped_products = 0

    try:

        # ====================================================
        # Process every CSV row
        # ====================================================

        for _, row in df.iterrows():

            # ------------------------------------------------
            # Product information
            # ------------------------------------------------

            product_name = clean_text(
                row["Item name"]
            )

            # Product name is required
            if not product_name:

                print(
                    "Skipping row because product name is missing."
                )

                skipped_products += 1

                continue

            brand = clean_text(
                row["Brand_Name"]
            )

            category = clean_text(
                row["Category"]
            )

            sub_category = clean_text(
                row["Sub_Category"]
            )

            ingredients = clean_text(
                row["Ingredients"]
            )

            # IMPORTANT:
            # Serving size can contain values such as:
            # "30 g"
            # "50 g"
            # "1 pack"
            #
            # Therefore it must remain TEXT.

            serving_size = clean_text(
                row["Serving_Size_g"]
            )

            price_inr = clean_number(
                row["Price_INR"]
            )

            source_of_data = clean_text(
                row["Source_of_Data"]
            )

            collection_date = clean_text(
                row["Collection_Date"]
            )

            collected_by = clean_text(
                row["Collected_By"]
            )

            remarks = clean_text(
                row["Remarks"]
            )

            # ------------------------------------------------
            # Check for duplicate product
            # ------------------------------------------------

            existing_product = db.query(Product).filter(
                Product.product_name == product_name,
                Product.brand == brand
            ).first()

            if existing_product:

                skipped_products += 1

                continue

            # ------------------------------------------------
            # Create Product
            # ------------------------------------------------

            new_product = Product(

                product_name=product_name,

                brand=brand,

                category=category,

                sub_category=sub_category,

                # Kaggle dataset does not contain barcode
                barcode=None,

                serving_size=serving_size,

                ingredients=ingredients,

                price_inr=price_inr,

                source_of_data=source_of_data,

                collection_date=collection_date,

                collected_by=collected_by,

                remarks=remarks
            )

            db.add(new_product)

            # ------------------------------------------------
            # Get generated product ID
            # ------------------------------------------------

            db.flush()

            # ------------------------------------------------
            # Create Nutrition
            # ------------------------------------------------

            new_nutrition = Nutrition(

                product_id=new_product.id,

                calories=clean_number(
                    row["Calories_kcal"]
                ),

                carbohydrates=clean_number(
                    row["Carbohydrates_g"]
                ),

                protein=clean_number(
                    row["Proteins_g"]
                ),

                total_fat=clean_number(
                    row["Total_Fat_g"]
                ),

                saturated_fat=clean_number(
                    row["Saturated_Fat_g"]
                ),

                trans_fat=clean_number(
                    row["Trans_Fat_g"]
                ),

                sugar=clean_number(
                    row["Sugar_g"]
                ),

                sodium=clean_number(
                    row["Sodium_mg"]
                ),

                fiber=clean_number(
                    row["Dietary_Fiber_g"]
                ),

                cholesterol=clean_number(
                    row["Cholesterol_mg"]
                ),

                calcium=clean_number(
                    row["Calcium_mg"]
                ),

                vitamin=clean_text(
                    row["Vitamin"]
                ),

                iron=clean_number(
                    row["Iron_mg"]
                )
            )

            db.add(new_nutrition)

            inserted_products += 1

            inserted_nutrition += 1

            # ------------------------------------------------
            # Show progress every 50 products
            # ------------------------------------------------

            if inserted_products % 50 == 0:

                print(
                    f"Imported {inserted_products} products..."
                )

        # ====================================================
        # Save everything
        # ====================================================

        db.commit()

        print()
        print("====================================")
        print("NutriVision import completed")
        print("====================================")

        print(
            f"Products inserted: {inserted_products}"
        )

        print(
            f"Nutrition records inserted: {inserted_nutrition}"
        )

        print(
            f"Products skipped: {skipped_products}"
        )

        print()

    except Exception as e:

        # ----------------------------------------------------
        # Undo everything if any error occurs
        # ----------------------------------------------------

        db.rollback()

        print()
        print("====================================")
        print("Import failed")
        print("====================================")

        print()
        print("No changes were saved.")

        print()
        print("Error:")
        print(e)

    finally:

        db.close()


# ============================================================
# START PROGRAM
# ============================================================

if __name__ == "__main__":

    import_data()