# 01 — Hospital Data Setup

Environment validation and first clinical-data ingestion.

## Contents
- `scripts/verify_environment.py` — prints Python/pandas/NumPy/Matplotlib versions to validate the toolchain (runnable from any directory).
- `data/patients.csv` — the patient cohort dataset (real project data, do not delete).
- `notebooks/patients_analysis.ipynb` — ingests the CSV, computes descriptive statistics, draws the TP2 `plt.plot` of Cholesterol vs. Age, and an Age-vs-Cholesterol scatter colored by Blood Pressure.

## Run
```bash
python scripts/verify_environment.py          # from anywhere
jupyter lab notebooks/patients_analysis.ipynb # Step-0 cell resolves all paths
```

## TP2 — Steps 4 & 5: GitHub and `requirements.txt`

**Step 4 (version control).** Turn the analysis folder into a shared Git
repository and push the first commit:

```bash
git init
git add .
git commit -m "HospitalDataAnalysis: first patient cohort analysis"
git remote add origin https://github.com/<user>/HospitalDataAnalysis.git
git push -u origin main
```

A `.gitignore` keeps generated artifacts out of the history — this project
ignores `__pycache__/`, `.venv/`, and `.ipynb_checkpoints/` (see the
repository-root `.gitignore` for the full unified list).

**Step 5 (environment sharing).** Make the toolchain reproducible for anyone
who clones the repository:

```bash
python -m venv .venv && source .venv/bin/activate   # fresh environment
pip freeze > requirements.txt                       # pin the exact versions
pip install -r requirements.txt                     # reproduce them anywhere
```

The same workflow is applied at the repository level: the root
`requirements.txt` pins the unified toolchain shared by the APDS and TAI
tracks, so a single `pip install -r requirements.txt` reproduces every
notebook environment.
