#!/usr/bin/env python3
"""Strip outputs/execution counts from every committed Jupyter notebook.

Keeps the repository's .ipynb files clean and lightweight (``outputs: []``,
``execution_count: null``) while preserving all source cells and metadata.

Usage (from the repository root, with the repo .venv active):

    python scripts/clean_notebooks.py [--dry-run]

The script skips ``.venv/``, ``.git/`` and ``.ipynb_checkpoints/`` trees and
writes a short summary to stdout (no report file is left behind).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SKIP_PARTS = {".venv", "venv", ".git", ".ipynb_checkpoints", ".pytest_cache", "node_modules"}


def iter_notebooks(root: Path):
    for nb_path in root.rglob("*.ipynb"):
        if any(part in SKIP_PARTS for part in nb_path.parts):
            continue
        yield nb_path


def clean_notebook(nb_path: Path) -> tuple[int, int]:
    """Strip outputs from one notebook. Returns (n_cells, n_outputs_removed)."""
    with nb_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    removed = 0
    for cell in data.get("cells", []):
        if cell.get("cell_type") == "code":
            removed += len(cell.get("outputs", []))
            cell["outputs"] = []
            cell["execution_count"] = None
        cell.get("metadata", {}).pop("execution", None)

    with nb_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return len(data.get("cells", [])), removed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="report what would be cleaned without writing")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    cleaned, outputs_removed = 0, 0
    for nb_path in iter_notebooks(root):
        if args.dry_run:
            with nb_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            n_out = sum(len(c.get("outputs", [])) for c in data.get("cells", []) if c.get("cell_type") == "code")
            print(f"[dry-run] {nb_path.relative_to(root)}: {len(data.get('cells', []))} cells, {n_out} outputs")
            outputs_removed += n_out
            cleaned += 1
        else:
            n_cells, n_out = clean_notebook(nb_path)
            outputs_removed += n_out
            cleaned += 1

    print(f"\nNotebooks {'checked' if args.dry_run else 'cleaned'}: {cleaned}")
    print(f"Outputs removed: {outputs_removed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
