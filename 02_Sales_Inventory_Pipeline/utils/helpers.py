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
