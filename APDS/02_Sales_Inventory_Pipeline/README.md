# 02 — Sales Inventory Pipeline

Modular text-processing pipeline: raw inventory lines to `Product` objects and valuation charts.

## Contents
- `utils/helpers.py` — `clean_lines`, `clean_lines_loop`, `parse_products`, `save_processed_data` (unit-tested).
- `utils/product.py` — the `Product` class with `total_value()` and a formatted `__str__`.
- `data/raw/data.txt` — raw inventory data including a deliberately corrupted row (real project data, do not delete).
- `data/processed/` — generated pipeline output (cleaned lines + CSV summary); gitignored, only the folder is tracked via `.gitkeep`.
- `scripts/create_products.py` — CLI pipeline; paths resolve from the project folder, so it runs from any CWD.
- `notebooks/analysis.ipynb` — loop-vs-comprehension cleaning comparison, `Product.__str__` showcase, processed-data persistence, valuation bar chart.

## Run
```bash
python scripts/create_products.py     # works from repo root, project dir, or scripts/
```

Each run writes two artifacts under `data/processed/`: `cleaned_data.txt`
(the cleaned `name,price,quantity` lines) and `products_summary.csv` (the
same records with a computed `total_value` column). Per the Tutorial 03
pipeline structure, processed data is a generated artifact — it is never
committed; the `data/processed/` folder itself stays tracked via `.gitkeep`
(the same convention as `TAI/outputs/`).
