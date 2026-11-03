import tracemalloc
import os
from generate_dataset.py import generate_large_csv
from streaming_solutions import read_all_inefficient, stream_records

def run_benchmark():
    filename = "large_patients.csv"
    if not os.path.exists(filename):
        generate_large_csv(filename, total_rows=1000000)

    # 1. Test Inefficient Loading
    tracemalloc.start()
    records = read_all_inefficient(filename)
    _, peak_bad = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"Inefficient Peak Memory: {peak_bad / (1024*1024):.2f} MB")
    del records

    # 2. Test Generator Streaming
    tracemalloc.start()
    stream = stream_records(filename)
    count = 0
    for r in stream:
        if int(r["BloodPressure"]) > 140:
            count += 1
    _, peak_good = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"Generator Peak Memory:   {peak_good / (1024*1024):.4f} MB")
    print(f"Total Hypertensive Rows: {count:,}")

if __name__ == "__main__":
    run_benchmark()
