import csv
import os

def generate_large_csv(filepath="large_patients.csv", total_rows=1000000):
    if os.path.exists(filepath):
        print(f"Dataset '{filepath}' already exists.")
        return
    print(f"Generating {total_rows:,} patient records in '{filepath}'...")
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["PatientID", "Age", "BloodPressure"])
        for i in range(total_rows):
            w.writerow([f"P{i:07d}", 20 + (i % 60), 110 + (i % 50)])
    print("Generation complete.")

if __name__ == "__main__":
    generate_large_csv()
