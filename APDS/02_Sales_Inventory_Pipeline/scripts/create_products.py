import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import clean_lines, parse_products, Product

def main():
    raw_path = os.path.join("data", "raw", "data.txt")
    if not os.path.exists(raw_path):
        print(f"[Error] Target data not found: {raw_path}")
        sys.exit(1)

    with open(raw_path, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    cleaned = clean_lines(raw_lines)
    records = parse_products(cleaned)

    products = []
    total_revenue = 0.0

    print("\n--- Inventory Valuation ---")
    for name, price, qty in records:
        prod = Product(name, price, qty)
        products.append(prod)
        val = prod.total_value()
        total_revenue += val
        print(f"{prod.name:10s}: {val:.1f}")

    print("---------------------------")
    print(f"Total Sales: {total_revenue:.1f}")

if __name__ == "__main__":
    main()
