# 09 — Iris Exploratory Data Analysis

The closing EDA project on Fisher's iris dataset: structure, per-species
profiles, correlation with its Simpson-twist, the setosa rule, the
versicolor/virginica overlap, and a pair grid.

## Contents
- `notebooks/01_iris_eda.ipynb` — loads sklearn's bundled iris (offline, nothing
  written to disk): structure and balance check (150 rows, 3 x 50 species, zero
  missing), per-species mean/std profiles, correlation heatmap with the
  within-setosa comparison (sepal corr -0.12 pooled vs +0.74 inside setosa), the
  petal-length rule that classifies setosa 100% on this data (threshold 2.5 cm,
  drawn on the chart), the petal scatter with the 0.6 cm versicolor/virginica
  overlap zone marked, per-measurement distribution panels, box plot, pair grid -
  each figure rendered to memory and audited non-blank before being closed.
- Data comes from `sklearn.datasets.load_iris` at runtime; no `data/` folder,
  no generated artifacts.

## Conventions
Same as the other APDS projects: Step-0 portable bootstrap (runs from the repo
root, the project folder or `notebooks/`, and on Google Colab), output-free
committed notebooks, figure audit in memory.
