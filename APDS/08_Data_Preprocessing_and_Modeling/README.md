# 08 — Data Preprocessing & Modeling

End-to-end scikit-learn preparation and classification pipelines.

## Notebooks
- `notebooks/01_medical_preprocessing_walkthrough.ipynb` — text standardization, mode/median imputation (Pandas 3.x safe), IQR outlier capping, one-hot encoding, standard scaling on `data/messy_medical.csv`; the four TP5 Exercise 01 Task 2 Seaborn charts (Age vs BloodPressure by gender, cholesterol distribution by diagnosis, melted numeric comparison, mean blood-pressure pivot heatmap) and the cap-versus-remove outlier discussion (6 of 10 rows survive removal; capping keeps all 10).
- `notebooks/02_titanic_end_to_end_pipeline.ipynb` — Titanic cleaning, feature engineering, encoding, split, scaling, Logistic Regression vs. KNN (dataset via `seaborn.load_dataset`, requires internet); plus printed EDA (sex/class survival structure, missingness, the `alive` target duplicate), the documented `name`-column quirk of the seaborn copy (no `name`/`ticket`/`cabin`, so no classic Title feature; `who`/`adult_male` as the existing proxies), skew table for the scaled columns with the no-log justification, the scaled-vs-unscaled comparison (KNN {UNSCALED_KNN:.4f} -> {SCALED_KNN:.4f}, LR flat), and confusion matrices with the keep-LR justification.
