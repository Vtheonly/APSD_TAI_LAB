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
