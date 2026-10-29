# What changed in this update

## Bugs fixed
- `POST /reference-values/` crashed (`daily_value` vs `reference_value`, missing `basis`)
- Open Food Facts lookup never matched (v3 returns `status: "success"`, code expected `1`); now uses v2 and accepts both
- Analysis endpoint returned 404 because reference values were never created - they are now seeded on startup
- Analysis results were never shown in the UI - now displayed on the product page
- Barcode scanning was a stub (`console.log`) - now fully connected
- Fake sample data on the home page replaced with a real product from the dataset
- `test_analysis.py` import problem - replaced by a proper pytest suite
- Camera stayed on when leaving the scan page - now cleaned up
- Search wildcards (`%`, `_`) typed by users are now matched literally
- Duplicate barcode now returns a clean 409 instead of a server error
- `/database-test` no longer leaks error details

## Improvements
- Per-100 g normalisation (dataset mixes per-100 g and per-serving rows)
- Nutrient-specific traffic lights (high fibre/protein is good; high sugar/fat/sodium is not), stricter limits for drinks
- Ingredient analysis: parsing, nested lists, flags, allergens, top-ingredient warnings
- CSV cleaning: decimal commas, `<x` values, BOM, symbols, zero-as-missing, data-quality notes
- Pagination and name-or-brand search
- Optional API-key protection for write endpoints; CORS and API URL configurable
- `get_db` shared in one place instead of copied into 5 files
- `requirements.txt`, `.env.example`, README, automated tests
- Removed the stray `package.json` from `backend/`
