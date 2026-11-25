# 00 — Introduction Exercises (TP1)

Theory exercises for Chapter 1 (*Introduction to Data Science*): matching
everyday projects to the data types they produce, to the **8-step Data
Science Workflow**, and to the professional roles that deliver them.

> **Source status.** The authoritative `TP1_Chapter_Introduction` handout
> (1 p., M. BOUSTIL, IA2 - AP_DS 2025/2026) is **not distributed inside this
> repository**. The exercise *structure* implemented here (Exercise 1 — five
> domain scenarios; Exercise 2 — a 5-year heart-disease risk study, the roles
> involved, and critical-thinking questions) follows the verified working
> spec recorded in GitHub issue #2. The five scenario domains themselves are
> pending confirmation against the handout and are marked
> `TO_CONFIRM_FROM_TP1_PDF` in the notebook — nothing outside that structure
> has been invented.

## Contents
- `notebooks/01_introduction_exercises.ipynb` — Exercise 1 (scenario → data
  types → workflow steps) and Exercise 2 (heart-disease risk study roles and
  critical thinking), as a structured markdown + Python workbook.
- No data files: this project is a reflection exercise, not a pipeline.

## Run
```bash
jupyter lab notebooks/01_introduction_exercises.ipynb  # Step-0 cell resolves all paths
```

## Concepts exercised (Chapter 1)
- Structured vs. unstructured data; quantitative vs. categorical features.
- The 8-step Data Science Workflow: Problem Definition → Data Collection →
  Data Cleaning & Preparation → EDA → Modeling → Evaluation → Deployment →
  Monitoring.
- Role archetypes (Data Scientist, ML Engineer, Data Engineer, Domain
  Expert, BI Analyst) and how a single clinical study spans all of them.

See `APDS/01_Hospital_Data_Setup/` for the first *practical* project (TP2).
