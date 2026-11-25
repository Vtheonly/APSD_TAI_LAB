import csv
from typing import Generator, Dict

def read_all_inefficient(filepath: str) -> list:
    # Loads entire file into memory as a list of dicts (High Memory Usage)
    with open(filepath, mode='r', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def stream_records(filepath: str) -> Generator[Dict[str, str], None, None]:
    # Generator stream: keeps one row in memory at a time (Flat Memory Usage)
    with open(filepath, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row


# ---------------------------------------------------------------------------
# Tutorial 03 (v2) — Exercise 6: "Give solution for one million products."
#
# Same streaming discipline as the 1M-patients case above, applied to the
# Sales_project domain of APDS/02: rows follow the Product semantics
# (name, price, quantity) used across the sales pipeline.
# ---------------------------------------------------------------------------
def generate_large_products_csv(filepath="large_products.csv", total_rows=1000000):
    """Create a deterministic 1M-row product CSV (name, price, quantity).

    Mirrors generate_dataset.generate_large_csv: deterministic row formulas
    (no RNG), skips regeneration when the file already exists.
    """
    import os

    if os.path.exists(filepath):
        print(f"Dataset '{filepath}' already exists.")
        return
    print(f"Generating {total_rows:,} product records in '{filepath}'...")
    names = ["Laptop", "Phone", "Tablet", "Monitor", "Keyboard", "Mouse", "Printer", "Scanner"]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Name", "Price", "Quantity"])
        for i in range(total_rows):
            name = names[i % len(names)]
            price = 100 + (i % 40) * 25          # 100..975 in steps of 25
            quantity = 1 + (i % 50)              # 1..50
            w.writerow([name, price, quantity])
    print("Generation complete.")


def stream_products(filepath: str):
    """Yield one (name, price, quantity) tuple per row — Product semantics.

    Streams instead of materializing a list, so a 1M-product inventory is
    processed in O(1) memory. Malformed rows are skipped with a warning,
    exactly like utils.parse_products in the Sales_project.
    """
    with open(filepath, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                name = row["Name"].strip().replace('"', '')
                price = float(row["Price"])
                quantity = int(row["Quantity"])
            except (ValueError, TypeError, KeyError):
                print(f"[Warning] Skipping malformed product row: {row}")
                continue
            yield (name, price, quantity)


def total_inventory_value(filepath: str) -> float:
    """Streaming sum of price * quantity over all products (Ex 6 metric)."""
    total = 0.0
    for _name, price, quantity in stream_products(filepath):
        total += price * quantity
    return total

