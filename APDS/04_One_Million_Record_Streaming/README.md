# 04 — One-Million Record Streaming

Memory autopsy of large CSV loading: list-of-dicts vs. generator streaming —
on **both** million-record exercises of the course: 1M patients
(Chapter 3 Part 2 memory problem) and 1M products (Tutorial 03 v2,
Exercise 6: "Give solution for one million products").

## Contents
- `generate_dataset.py` — `generate_large_csv` (patients; deterministic, skips regeneration if the file exists).
- `streaming_solutions.py` — `read_all_inefficient`, `stream_records`, plus the product-side solution: `generate_large_products_csv`, `stream_products` (yields `(name, price, quantity)` tuples — the `Product` semantics of `APDS/02`, malformed rows skipped with a warning like `utils.parse_products`), `total_inventory_value` (streaming `price * quantity` sum).
- `memory_benchmark.py` — benchmark harness for both datasets (paths resolve from the script location; runs from any CWD): `run_benchmark()` (patients) and `run_products_benchmark()` (products).
- `streaming_analysis.ipynb` — interactive tracemalloc comparison, patients then products (§4).
- `large_patients.csv`, `large_products.csv` — **generated at runtime and git-ignored** (deterministically regenerable, byte-identical every time).

## Run
```bash
python memory_benchmark.py        # benchmarks BOTH 1M patients and 1M products
```
