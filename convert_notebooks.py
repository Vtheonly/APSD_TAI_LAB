
import json
from pathlib import Path

ROOT = Path(".")
created = 0
failed = []

for notebook_path in ROOT.rglob("*.ipynb"):
    try:
        # Skip virtual environments and dependency folders
        if any(
            part in {".venv", "venv", "node_modules", ".git"}
            for part in notebook_path.parts
        ):
            continue

        with notebook_path.open("r", encoding="utf-8") as f:
            notebook = json.load(f)

        output_path = notebook_path.with_suffix(".txt")

        with output_path.open("w", encoding="utf-8") as f:
            for index, cell in enumerate(notebook.get("cells", []), 1):
                cell_type = cell.get("cell_type", "unknown").upper()

                f.write("=" * 80 + "\n")
                f.write(f"CELL {index} | {cell_type}\n")
                f.write("=" * 80 + "\n\n")

                source = cell.get("source", [])
                f.write("".join(source) if isinstance(source, list) else source)
                f.write("\n\n")

        created += 1
        print(f"Created: {output_path}")

    except Exception as error:
        failed.append((notebook_path, str(error)))

print("\n" + "=" * 50)
print("CONVERSION REPORT")
print("=" * 50)
print(f"Successfully converted: {created}")
print(f"Failed: {len(failed)}")

for path, error in failed:
    print(f"FAILED: {path} | {error}")
