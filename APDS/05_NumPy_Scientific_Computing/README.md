# 05 — NumPy Scientific Computing

Vectorized numerical analysis exercises.

## Notebooks
- `notebooks/01_temperature_analysis.ipynb` — 7-day x 3-city temperature matrix: axis-wise maxima, `argmax`/`unravel_index` lookup, vstack of city means, boolean masking.
- `notebooks/02_student_grades_analysis.ipynb` — 100 students x 5 modules: summary statistics, percentiles, boolean masking and boxplots (Matplotlib 3.9+ `tick_labels` with a version-safe fallback); Task 1 `mean_per_student` (`grades_of_students` alias, checked against a row-by-row recomputation) and three Extra Practice tasks (all grades above 15 with the `>= 15` boundary comparison, top 5 students with `np.argsort`, module with the highest average).
