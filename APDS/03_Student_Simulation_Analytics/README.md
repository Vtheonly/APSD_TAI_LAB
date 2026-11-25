# 03 — Student Simulation & Analytics

Synthetic student cohort generation (seeded), enrichment and cohort statistics with an exported report.

## Contents
- `students.py` — `generate_students` (seeded birth dates 2000-2006 and grades).
- `analysis.py` — `enrich_student_data`, `compute_cohort_statistics`.
- `main.ipynb` — runs the pipeline and writes `results/report.txt`.
- `results/report.txt` — generated audit report (deterministic, re-created by the notebook).

Both modules are covered by `tests/test_apds_modules.py` at the repository root.
