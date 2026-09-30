# NutriVision

## Smart Food Label & Ingredient Analysis System

NutriVision is a web-based food analysis system designed to help users understand packaged food products through their nutritional information and ingredient data.

The system allows users to search for packaged food products and view their product information, ingredients, nutritional values, and nutrition-based analysis.

The project is being developed as an academic software and machine learning project with a focus on making food information easier to understand.

---

## Project Overview

Packaged food products contain important information such as calories, sugar, fat, sodium, protein, ingredients, and other nutritional values.

However, nutritional labels can be difficult for consumers to understand.

NutriVision aims to provide a simple platform where users can:

- Search for packaged food products
- View product information
- View ingredient information
- View nutritional information
- Analyze nutritional values
- Compare nutritional values with reference values
- Understand the nutritional contribution of a product
- Receive simplified food-related insights

A barcode scanning feature is also included in the project structure and is planned for further development.

---

## Current Project Flow

```text
User
 |
 v
NutriVision Homepage
 |
 +-----------------------+
 |                       |
 v                       v
Search Product       Scan Product
 |                       |
 v                       |
PostgreSQL Database      |
 |                       |
 v                       |
Product Details <--------+
 |
 +----------------------+
 |                      |
 v                      v
Nutrition Data       Ingredients
 |
 v
Nutrition Analysis
 |
 v
Reference Value Comparison
 |
 v
Percentage Contribution
 |
 v
Nutritional Classification