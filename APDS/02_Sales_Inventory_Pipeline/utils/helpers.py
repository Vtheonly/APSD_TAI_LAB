def clean_lines_loop(lines: list) -> list:
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if stripped != "" and stripped != "\n":
            cleaned.append(stripped)
    return cleaned

def clean_lines(lines: list) -> list:
    return [stripped for line in lines if (stripped := line.strip())]

def parse_products(lines: list) -> list:
    parsed = []
    for line in lines:
        parts = line.split(",")
        if len(parts) != 3:
            print(f"[Warning] Skipping malformed field count: {line}")
            continue
        try:
            name = parts[0].strip().replace('"', '')
            price = float(parts[1].strip())
            qty = int(parts[2].strip())
            parsed.append((name, price, qty))
        except ValueError as err:
            print(f"[Warning] Parsing error in '{line}': {err}")
            continue
    return parsed


def save_processed_data(records: list, processed_dir) -> tuple:
    """Persist the parsed inventory as the project's processed-data artifact.

    Writes two files inside ``processed_dir`` (normally ``data/processed/``):
    ``cleaned_data.txt`` (one ``name,price,quantity`` line per record) and
    ``products_summary.csv`` (the same records plus a computed
    ``total_value`` column). Returns the two written paths.
    """
    txt_path = processed_dir / "cleaned_data.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        for name, price, qty in records:
            f.write(f"{name},{price},{qty}\n")

    csv_path = processed_dir / "products_summary.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("name,price,quantity,total_value\n")
        for name, price, qty in records:
            f.write(f"{name},{price},{qty},{price * qty}\n")

    return txt_path, csv_path
