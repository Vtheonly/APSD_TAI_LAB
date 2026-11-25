import os
import tracemalloc
from pathlib import Path

from generate_dataset import generate_large_csv
from streaming_solutions import read_all_inefficient, stream_records

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


if __name__ == "__main__":
    run_benchmark()
