# 08 — Data Preprocessing & Modeling

End-to-end scikit-learn preparation and classification pipelines.

## Notebooks
- `notebooks/01_medical_preprocessing_walkthrough.ipynb` — text standardization, mode/median imputation (Pandas 3.x safe), IQR outlier capping, one-hot encoding, standard scaling on `data/messy_medical.csv`; the four TP5 Exercise 01 Task 2 Seaborn charts (Age vs BloodPressure by gender, cholesterol distribution by diagnosis, melted numeric comparison, mean blood-pressure pivot heatmap) and the cap-versus-remove outlier discussion (6 of 10 rows survive removal; capping keeps all 10).
- `notebooks/02_titanic_end_to_end_pipeline.ipynb` — Titanic cleaning, feature engineering, encoding, split, scaling, Logistic Regression vs. KNN (dataset via `seaborn.load_dataset`, requires internet).
