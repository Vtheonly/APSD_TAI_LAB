import json
from pathlib import Path
from datetime import datetime

ROOT = Path(".")
REPORT = ROOT / "jupyter_cleanup_report.txt"

cleaned = []
failed = []

for notebook in ROOT.rglob("*.ipynb"):
    try:
        with notebook.open("r", encoding="utf-8") as f:
            data = json.load(f)

        removed_outputs = 0
        removed_images = 0

        for cell in data.get("cells", []):
            if cell.get("cell_type") == "code":
                removed_outputs += len(cell.get("outputs", []))
                cell["outputs"] = []
                cell["execution_count"] = None

            # Remove cell execution metadata, preserve source and other metadata.
            cell.get("metadata", {}).pop("execution", None)

        # Preserve notebook structure and source code.
        with notebook.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
            f.write("\n")

        cleaned.append(
            f"{notebook} | Outputs removed: {removed_outputs}"
        )

    except Exception as e:
        failed.append(f"{notebook} | ERROR: {e}")

with REPORT.open("w", encoding="utf-8") as f:
    f.write("JUPYTER NOTEBOOK CLEANUP REPORT\n")
    f.write(f"Date: {datetime.now()}\n")
    f.write("=" * 60 + "\n\n")

    f.write(f"Successfully cleaned: {len(cleaned)}\n")
    f.write(f"Failed: {len(failed)}\n\n")

    f.write("CLEANED NOTEBOOKS:\n")
    f.write("\n".join(cleaned))

    f.write("\n\nFAILED NOTEBOOKS:\n")
    f.write("\n".join(failed))

print(f"Cleaned: {len(cleaned)} notebooks")
print(f"Failed: {len(failed)} notebooks")
print(f"Report: {REPORT}")