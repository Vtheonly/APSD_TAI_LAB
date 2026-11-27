# 00 — Introduction Exercises (TP1)

Theory exercises for Chapter 1 (*Introduction to Data Science*): classifying
five application scenarios into the fields **Data Science, Machine Learning,
AI, Big Data and Business Intelligence**, and decomposing a 5-year
heart-disease risk study into its professional roles.

> **Source status.** The authoritative `TP1_Chapter_Introduction` handout
> (1 p., IA2 - AP_DS 2025/2026) is archived in this repository at
> `APDS/docs/TP1_Chapter_Introduction.pdf` (scanned print-to-PDF; text
> recovered by OCR). The five scenarios of Exercise 1, the hospital scenario
> with its five specialist roles, tasks (a)–(e) and the two
> critical-thinking questions of Exercise 2 are transcribed exactly from it.
> The model answers are this project's own, built strictly with the Chapter 1
> vocabulary (field matrix and role boundaries of vault note
> `01.2. The Modern Data Ecosystem and Professional Roles`).

## Contents
- `notebooks/01_introduction_exercises.ipynb` — Exercise 1 (five scenarios →
  field classification with justification) and Exercise 2 (role matching
  (a)–(e) + the two critical-thinking questions), as a structured markdown +
  Python workbook.
- No data files: this project is a reflection exercise, not a pipeline.

## Run
```bash
jupyter lab notebooks/01_introduction_exercises.ipynb  # Step-0 cell resolves all paths
```

## Concepts exercised (Chapter 1)
- The five application fields and their boundaries: Data Science, Machine
  Learning, Artificial Intelligence, Big Data (Volume, Velocity, Variety)
  and Business Intelligence.
- The 8-step Data Science Workflow: Problem Definition → Data Collection →
  Data Cleaning & Preparation → EDA → Modeling → Evaluation → Deployment →
  Monitoring (used to justify each role assignment).
- The five project roles — Data Analyst, Data Scientist, Data Engineer, ML
  Engineer, Business Analyst — and why the critical-thinking role pairs are
  complementary rather than interchangeable.

See `APDS/01_Hospital_Data_Setup/` for the first *practical* project (TP2).
