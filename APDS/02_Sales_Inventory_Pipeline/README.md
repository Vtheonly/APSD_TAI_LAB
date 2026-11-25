# 02 — Sales Inventory Pipeline

Modular text-processing pipeline: raw inventory lines to `Product` objects and valuation charts.

## Contents
- `utils/helpers.py` — `clean_lines`, `clean_lines_loop`, `parse_products` (unit-tested).
- `utils/product.py` — the `Product` class with `total_value()`.
- `data/raw/data.txt` — raw inventory data including a deliberately corrupted row (real project data, do not delete).
- `scripts/create_products.py` — CLI pipeline; paths resolve from the project folder, so it runs from any CWD.
- `notebooks/analysis.ipynb` — loop-vs-comprehension cleaning comparison + valuation bar chart.

## Run
```bash
python scripts/create_products.py     # works from repo root, project dir, or scripts/
```
