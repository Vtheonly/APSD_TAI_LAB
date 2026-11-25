#!/usr/bin/env python3
"""Headless end-to-end execution of every notebook in the repository.

Runs 100% of the ``.ipynb`` files (APDS + TAI) through
``jupyter nbconvert --execute`` in a temporary directory with the
non-interactive ``MPLBACKEND=Agg`` backend, then verifies that no cell
raised an exception and prints a per-notebook runtime summary.

Usage (from the repository root, with the repo .venv active):

    python scripts/execute_notebooks.py [--pattern TAI] [--keep]

Exit code 0 only when every notebook executed without errors.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKIP_PARTS = {".venv", "venv", ".git", ".ipynb_checkpoints", ".pytest_cache", "node_modules"}


def collect_notebooks(pattern: str | None) -> list[Path]:
    nbs = [
        p
        for p in sorted(REPO_ROOT.rglob("*.ipynb"))
        if not any(part in SKIP_PARTS for part in p.parts)
    ]
    if pattern:
        nbs = [p for p in nbs if pattern in str(p.relative_to(REPO_ROOT))]
    return nbs


def execute_notebook(nb_path: Path, out_dir: Path) -> tuple[bool, float, int, int]:
    """Execute one notebook. Returns (ok, seconds, n_cells, n_cell_errors)."""
    env = dict(os.environ)
    env["MPLBACKEND"] = "Agg"
    t0 = time.perf_counter()
    result = subprocess.run(
        [
            sys.executable, "-m", "jupyter", "nbconvert",
            "--to", "notebook",
            "--execute",
            "--ExecutePreprocessor.timeout=900",
            f"--output-dir={out_dir}",
            str(nb_path),
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    dt = time.perf_counter() - t0
    if result.returncode != 0:
        return False, dt, 0, -1

    executed = out_dir / nb_path.name
    n_err, n_cells = 0, 0
    if executed.exists():
        with executed.open("r", encoding="utf-8") as f:
            data = json.load(f)
        n_cells = len(data.get("cells", []))
        for cell in data.get("cells", []):
            for output in cell.get("outputs", []):
                if output.get("output_type") == "error":
                    n_err += 1
    return n_err == 0, dt, n_cells, n_err


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pattern", default=None,
                        help="only execute notebooks whose path contains this substring")
    parser.add_argument("--jobs", type=int, default=4,
                        help="number of notebooks to execute concurrently (default 4)")
    parser.add_argument("--keep", action="store_true",
                        help="keep the temporary execution directory")
    args = parser.parse_args()

    notebooks = collect_notebooks(args.pattern)
    if not notebooks:
        print("No notebooks found.")
        return 1

    from concurrent.futures import ThreadPoolExecutor

    failures = []
    with tempfile.TemporaryDirectory(prefix="nbexec_", dir=str(REPO_ROOT.parent)) as td:
        out_dir = Path(td)
        print(f"Executing {len(notebooks)} notebooks headlessly (MPLBACKEND=Agg, jobs={args.jobs})...\n")
        print(f"{'Notebook':68s} | {'cells':>5s} | {'errors':>6s} | {'time (s)':>8s}")
        print("-" * 96)
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            results = list(pool.map(lambda nb: (nb, *execute_notebook(nb, out_dir)), notebooks))
        for nb_path, ok, dt, n_cells, n_err in results:
            rel = nb_path.relative_to(REPO_ROOT)
            print(f"{str(rel):68s} | {n_cells:5d} | {n_err:6d} | {dt:8.1f}")
            if not ok:
                failures.append((str(rel), n_err))

    print("-" * 96)
    if failures:
        print(f"FAILED notebooks: {len(failures)}")
        for rel, n_err in failures:
            print(f"  - {rel} ({n_err} cell errors)")
        return 1
    print(f"All {len(notebooks)} notebooks executed with 0 cell errors.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
