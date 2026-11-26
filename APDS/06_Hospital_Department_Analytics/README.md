# 06 — Hospital Department Analytics

Pandas indexing, risk scoring and pivot analytics on department data.

## Contents
- `data/hospital_original.csv` — source dataset (real project data).
- `data/hospital_risk.csv`, `data/city_summary.csv` — exports of notebook 02 (deterministically re-created on each run).
- `notebooks/01_hospital_indexing_and_slicing.ipynb` — custom label index, `.loc` vs `.iloc`, boolean filtering, department subsetting.
- `notebooks/03_hospital_matplotlib_vs_seaborn.ipynb` — Exercise 04: nine hospital charts (four Matplotlib: annotated bar, histogram with mean/median vlines and bin sensitivity, high-cost scatter, 1x3 shared-ylim panels; five Seaborn: barplot with hue, box + violin, correlation heatmap, pairplot, 2x2 overview dashboard), each rendered to memory and audited non-blank before being closed.
- `notebooks/02_hospital_risk_and_pivot_analytics.ipynb` — Exercise 03 Part 2 (task map for handout Tasks 1-11): TotalCost, AgeGroup, RiskScore/RiskCategory, groupby aggregations, mapping, pivot tables, CSV exports, bonus add/rename/drop, `HighCost` / `SatisfactionLevel` with the handout thresholds (the scale quirk `TotalCost > 60,000` and `Satisfaction >= 8` is documented, with a labelled sensitivity check), `CostRank`, imputation of a missing satisfaction before mapping, and `pivot_table` versus `groupby`.
