# 01 — Hospital Data Setup

Environment validation and first clinical-data ingestion.

## Contents
- `scripts/verify_environment.py` — prints Python/pandas/NumPy/Matplotlib versions to validate the toolchain (runnable from any directory).
- `data/patients.csv` — the patient cohort dataset (real project data, do not delete).
- `notebooks/patients_analysis.ipynb` — ingests the CSV, computes descriptive statistics and a Age-vs-Cholesterol scatter plot.

## Run
```bash
python scripts/verify_environment.py          # from anywhere
jupyter lab notebooks/patients_analysis.ipynb # Step-0 cell resolves all paths
```
