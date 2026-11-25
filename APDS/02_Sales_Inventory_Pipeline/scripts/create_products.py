import sys
from pathlib import Path

# Make the project's `utils` package importable no matter where the script is
# launched from (repo root, project folder, or elsewhere).
PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from utils import clean_lines, parse_products, Product


def main():
    # Resolve the raw data path from the project directory (not the CWD), so
    # the script works from the repository root or any other directory.
    raw_path = PROJECT_DIR / "data" / "raw" / "data.txt"
    if not raw_path.exists():
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
