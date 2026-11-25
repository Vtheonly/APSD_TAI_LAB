# APDS — Advanced Python & Data Science Coursework

This folder contains the **APDS coursework track**: eight self-contained,
numbered practical projects covering the full data-science workflow with
Python.

## Projects

| # | Project | Focus | Entry points |
|---|---------|-------|--------------|
| 01 | `01_Hospital_Data_Setup` | environment validation, first pandas ingestion | `notebooks/patients_analysis.ipynb`, `scripts/verify_environment.py` |
| 02 | `02_Sales_Inventory_Pipeline` | modular code, text parsing, OOP | `notebooks/analysis.ipynb`, `scripts/create_products.py`, `utils/` |
| 03 | `03_Student_Simulation_Analytics` | synthetic data generation & statistics | `main.ipynb`, `students.py`, `analysis.py` |
| 04 | `04_One_Million_Record_Streaming` | memory profiling, generators, CSV streaming | `streaming_analysis.ipynb`, `generate_dataset.py`, `memory_benchmark.py`, `streaming_solutions.py` |
| 05 | `05_NumPy_Scientific_Computing` | NumPy arrays, aggregation, boolean masking | `notebooks/01_temperature_analysis.ipynb`, `notebooks/02_student_grades_analysis.ipynb` |
| 06 | `06_Hospital_Department_Analytics` | pandas indexing, risk scoring, pivots | `notebooks/01_hospital_indexing_and_slicing.ipynb`, `notebooks/02_hospital_risk_and_pivot_analytics.ipynb` |
| 07 | `07_Monthly_Sales_Forecasting` | time series, feature engineering, visualization | `notebook.ipynb`, `utils.py` |
| 08 | `08_Data_Preprocessing_and_Modeling` | cleaning, encoding, scaling, scikit-learn pipelines | `notebooks/01_medical_preprocessing_walkthrough.ipynb`, `notebooks/02_titanic_end_to_end_pipeline.ipynb` |

## Conventions

- **Portable paths**: every notebook starts with a Step-0 bootstrap cell that
  locates its project folder by walking up from the current working directory
  (works from the repository root, the project folder, or `notebooks/`) and
  resolves all data paths from it. On Google Colab the repository is cloned
  into `/content/APSD_TAI_LAB` automatically.
- **Pandas 3.x / NumPy 2 / Matplotlib 3.10+ compatible**: no chained
  assignment (`df[col].fillna(..., inplace=True)`), no removed `labels=`
  boxplot argument (version-safe `tick_labels`/`labels` fallback).
- **Generated artifacts** (`large_patients.csv`, `07/data/`) are git-ignored;
  all committed `.csv` files under `data/` are real project data.
- Unit tests for the Python modules live in `tests/test_apds_modules.py` at
  the repository root.

See the repository root `README.md` for the unified environment setup (one
`.venv` + one root `requirements.txt`).
