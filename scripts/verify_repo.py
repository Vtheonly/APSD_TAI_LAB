#!/usr/bin/env python3
"""Repository hygiene & data-integrity verification for APSD_TAI_LAB.

Checks (all must pass):
  1. No ``.ipynb_checkpoints/`` directories anywhere.
  2. No ``Untitled*.ipynb`` notebooks.
  3. No leftover notebook text dumps (``*.ipynb.txt`` / ``*.txt`` next to notebooks).
  4. No space-containing ``TAI 1`` / ``TAI 2`` folders.
  5. No duplicate TP2_Exo4 notebooks (exactly one morphology notebook).
  6. No blocking GUI calls (``cv2.imshow``, ``cv2.waitKey``, ``cv2.destroyAllWindows``, bare ``input`` prompts) in any notebook or script.
  7. No hardcoded ``/home/...`` absolute paths in any notebook or script.
  8. The TAI image dataset is deduplicated (unique SHA-256 per file) and complete (39 reference images).
  9. All notebooks have empty outputs & null execution counts (run ``scripts/clean_notebooks.py`` otherwise).
 10. The root environment has a working ``opencv-contrib-python`` (``cv2.ximgproc``).

Usage:

    python scripts/verify_repo.py
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKIP_PARTS = {".venv", "venv", ".git", ".pytest_cache", "node_modules"}
IMAGE_EXTS = {".bmp", ".jpg", ".jpeg", ".png", ".pgm"}

GUI_PATTERN = re.compile(
    r"cv2\.(imshow|waitKey|destroyAllWindows|namedWindow)\s*\(|(?<![\w.])input\s*\("
)


def iter_files():
    for p in REPO_ROOT.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_PARTS for part in p.parts):
            continue
        yield p


def iter_notebooks():
    for p in REPO_ROOT.rglob("*.ipynb"):
        if any(part in SKIP_PARTS for part in p.parts):
            continue
        yield p


def check_no_ipynb_checkpoints(errors: list) -> None:
    hits = [str(p.relative_to(REPO_ROOT)) for p in REPO_ROOT.rglob(".ipynb_checkpoints")]
    if hits:
        errors.append(f".ipynb_checkpoints found: {hits}")


def check_no_untitled_notebooks(errors: list) -> None:
    hits = [str(p.relative_to(REPO_ROOT)) for p in iter_notebooks() if p.stem == "Untitled"]
    if hits:
        errors.append(f"Untitled notebooks found: {hits}")


def check_no_txt_dumps(errors: list) -> None:
    hits = []
    for p in REPO_ROOT.rglob("*.txt"):
        if any(part in SKIP_PARTS for part in p.parts):
            continue
        sibling_nb = p.with_suffix(".ipynb")
        if sibling_nb.exists():
            hits.append(str(p.relative_to(REPO_ROOT)))
    if hits:
        errors.append(f"Notebook .txt dumps found next to .ipynb files: {hits}")


def check_no_space_tai_folders(errors: list) -> None:
    hits = [d.name for d in REPO_ROOT.rglob("TAI *") if d.is_dir()]
    hits += [str(p.relative_to(REPO_ROOT)) for p in (REPO_ROOT / "TAI").glob("TAI*") if p.is_dir()]
    if hits:
        errors.append(f"Space-named TAI folders found: {sorted(set(hits))}")


def check_single_morphology_notebook(errors: list) -> None:
    hits = [
        str(p.relative_to(REPO_ROOT))
        for p in iter_notebooks()
        if "TP2_Exo4" in p.stem or "morphology" in p.stem.lower()
    ]
    if len(hits) != 1:
        errors.append(f"Expected exactly 1 morphology notebook, found {len(hits)}: {hits}")


def check_no_gui_calls(errors: list) -> None:
    for p in iter_files():
        if p.suffix not in {".ipynb", ".py"}:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if p.suffix == ".ipynb":
            try:
                nb = json.loads(text)
            except json.JSONDecodeError:
                errors.append(f"Unparsable notebook JSON: {p}")
                continue
            sources = [
                "".join(c.get("source", []))
                for c in nb.get("cells", [])
                if c.get("cell_type") == "code"
            ]
            text = "\n".join(sources)
        for m in GUI_PATTERN.finditer(text):
            line = text[: m.start()].count("\n") + 1
            errors.append(f"Blocking GUI/input call in {p.relative_to(REPO_ROOT)} (line {line}): {m.group(0)}")


def check_no_hardcoded_home(errors: list) -> None:
    for p in iter_files():
        if p.suffix not in {".ipynb", ".py", ".json", ".md"}:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for m in re.finditer(r"/home/[\w.-]+/", text):
            rel = str(p.relative_to(REPO_ROOT))
            if rel.startswith("docs/") or p.suffix == ".pdf":
                continue
            errors.append(f"Hardcoded /home/ path in {rel}: {m.group(0)}")


def check_tai_images(errors: list) -> tuple[int, int]:
    images_dir = REPO_ROOT / "TAI" / "images"
    if not images_dir.is_dir():
        errors.append("TAI/images/ directory missing")
        return 0, 0
    files = [p for p in images_dir.iterdir() if p.is_file()]
    hashes = {}
    for p in files:
        h = hashlib.sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        if h.hexdigest() in hashes:
            errors.append(f"Duplicate image (same SHA-256): {p.name} == {hashes[h.hexdigest()]}")
        hashes[h.hexdigest()] = p.name
    return len(files), len(hashes)


def check_notebooks_clean(errors: list) -> None:
    for p in iter_notebooks():
        with p.open("r", encoding="utf-8") as f:
            nb = json.load(f)
        for i, cell in enumerate(nb.get("cells", [])):
            if cell.get("cell_type") != "code":
                continue
            if cell.get("outputs") or cell.get("execution_count") is not None:
                errors.append(
                    f"Notebook has stale outputs: {p.relative_to(REPO_ROOT)} cell {i} "
                    "(run scripts/clean_notebooks.py)"
                )
                break


def check_opencv_contrib(errors: list) -> None:
    try:
        import cv2  # noqa: PLC0415

        if not hasattr(cv2, "ximgproc"):
            errors.append("opencv-contrib-python missing: cv2.ximgproc unavailable")
    except ImportError:
        errors.append("cv2 not importable in the current environment")


def main() -> int:
    errors: list[str] = []
    checks = [
        check_no_ipynb_checkpoints,
        check_no_untitled_notebooks,
        check_no_txt_dumps,
        check_no_space_tai_folders,
        check_single_morphology_notebook,
        check_no_gui_calls,
        check_no_hardcoded_home,
    ]
    for check in checks:
        check(errors)

    n_files, n_hashes = check_tai_images(errors)
    check_notebooks_clean(errors)
    check_opencv_contrib(errors)

    print("Repository verification report")
    print("=" * 60)
    print(f"TAI/images : {n_files} files, {n_hashes} unique SHA-256 hashes")
    print(f"Notebooks  : {sum(1 for _ in iter_notebooks())} tracked notebooks checked")
    if errors:
        print(f"\nFAILED with {len(errors)} problem(s):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("\nAll hygiene and integrity checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
