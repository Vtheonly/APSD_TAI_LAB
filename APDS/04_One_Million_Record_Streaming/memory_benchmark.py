import os
import tracemalloc
from pathlib import Path

from generate_dataset import generate_large_csv
from streaming_solutions import (
    generate_large_products_csv,
    read_all_inefficient,
    stream_records,
    total_inventory_value,
)

# Resolve every path from this script's folder so the benchmark runs from any
# working directory (repo root, project folder, or elsewhere).
PROJECT_DIR = Path(__file__).resolve().parent


def run_benchmark(filename="large_patients.csv"):
    filename = Path(filename)
    if not filename.is_absolute():
        filename = PROJECT_DIR / filename
    if not os.path.exists(filename):
        generate_large_csv(str(filename), total_rows=1000000)

    # 1. Test Inefficient Loading
    tracemalloc.start()
    records = read_all_inefficient(str(filename))
    _, peak_bad = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"Inefficient Peak Memory: {peak_bad / (1024 * 1024):.2f} MB")
    del records

    # 2. Test Generator Streaming
    tracemalloc.start()
    stream = stream_records(str(filename))
    count = 0
    for r in stream:
        if int(r["BloodPressure"]) > 140:
            count += 1
    _, peak_good = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"Generator Peak Memory:   {peak_good / (1024 * 1024):.4f} MB")
    print(f"Total Hypertensive Rows: {count:,}")


def run_products_benchmark(filename="large_products.csv"):
    """Tutorial 03 v2 — Exercise 6: the same benchmark on 1M product rows."""
    filename = Path(filename)
    if not filename.is_absolute():
        filename = PROJECT_DIR / filename
    if not os.path.exists(filename):
        generate_large_products_csv(str(filename), total_rows=1000000)

    # 1. Inefficient: materialize all product rows as dicts
    tracemalloc.start()
    rows = read_all_inefficient(str(filename))
    list_total = sum(float(r["Price"]) * int(r["Quantity"]) for r in rows)
    _, peak_bad = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"[Products] Inefficient Peak Memory: {peak_bad / (1024 * 1024):.2f} MB")
    del rows

    # 2. Generator: stream one (name, price, quantity) tuple at a time
    tracemalloc.start()
    stream_total = total_inventory_value(str(filename))
    _, peak_good = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"[Products] Generator Peak Memory:   {peak_good / (1024 * 1024):.4f} MB")
    print(f"[Products] Total Inventory Value:   {stream_total:,.0f} (matches list path: {list_total:,.0f})")


if __name__ == "__main__":
    run_benchmark()
    run_products_benchmark()
