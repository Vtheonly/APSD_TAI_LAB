"""Repository structure & hygiene checks (mirror of scripts/verify_repo.py)."""

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SKIP_PARTS = {".venv", "venv", ".git", ".pytest_cache", "node_modules"}


def iter_notebooks():
    for p in REPO_ROOT.rglob("*.ipynb"):
        if any(part in SKIP_PARTS for part in p.parts):
            continue
        yield p


def test_no_ipynb_checkpoints():
    hits = [p for p in REPO_ROOT.rglob(".ipynb_checkpoints")]
    assert not hits, f".ipynb_checkpoints found: {hits}"


def test_no_untitled_notebooks():
    hits = [p for p in iter_notebooks() if p.stem == "Untitled"]
    assert not hits, f"Untitled notebooks: {hits}"


def test_no_notebook_txt_dumps():
    hits = [p for p in REPO_ROOT.rglob("*.txt")
            if not any(part in SKIP_PARTS for part in p.parts)
            and p.with_suffix(".ipynb").exists()]
    assert not hits, f"stale .txt dumps: {hits}"


def test_no_space_named_tai_folders():
    hits = [p for p in (REPO_ROOT / "TAI").iterdir() if p.is_dir() and " " in p.name]
    assert not hits, f"space-named TAI folders: {hits}"


def test_single_morphology_notebook():
    hits = [p for p in iter_notebooks() if "morphology" in p.stem.lower() or "TP2_Exo4" in p.stem]
    assert len(hits) == 1, f"expected 1 morphology notebook, found: {hits}"


def test_expected_tai_lab_structure():
    expected = [
        "TAI/00_Environment_and_NumPy_Foundations",
        "TAI/01_TP1_Image_Fundamentals",
        "TAI/02_TP2_Noise_and_Spatial_Filtering",
        "TAI/03_TP2_Morphology_and_Contrast",
        "TAI/04_TP2_Super_Resolution",
        "TAI/images",
        "TAI/utils",
        "TAI/docs",
        "TAI/outputs",
    ]
    for rel in expected:
        assert (REPO_ROOT / rel).is_dir(), f"missing {rel}"
    assert (REPO_ROOT / "TAI" / "outputs" / ".gitkeep").is_file()


def test_expected_tai_utils_modules():
    for mod in ("env_io", "metrics", "noise", "basics", "filters", "morphology", "contrast", "super_res"):
        assert (REPO_ROOT / "TAI" / "utils" / f"{mod}.py").is_file(), f"missing TAI/utils/{mod}.py"


def test_no_subproject_requirements_or_gitignore():
    hits = []
    for pattern in ("APDS/*/requirements.txt", "TAI/*/requirements.txt", "APDS/*/.gitignore", "TAI/*/.gitignore"):
        hits += list(REPO_ROOT.glob(pattern))
    assert not hits, f"redundant sub-project config files: {hits}"


def test_no_blocking_gui_calls_in_notebooks_or_scripts():
    pattern = re.compile(r"cv2\.(imshow|waitKey|destroyAllWindows|namedWindow)\s*\(|(?<![\w.])input\s*\(")
    offenders = []
    for p in REPO_ROOT.rglob("*"):
        if not p.is_file() or p.suffix not in {".ipynb", ".py"}:
            continue
        if any(part in SKIP_PARTS for part in p.parts):
            continue
        text = p.read_text(encoding="utf-8")
        if p.suffix == ".ipynb":
            try:
                nb = json.loads(text)
            except json.JSONDecodeError:
                offenders.append(f"unparsable notebook {p}")
                continue
            text = "\n".join(
                "".join(c.get("source", [])) for c in nb.get("cells", []) if c.get("cell_type") == "code"
            )
        m = pattern.search(text)
        if m:
            offenders.append(f"{p.relative_to(REPO_ROOT)}: {m.group(0)}")
    assert not offenders, f"blocking GUI/input calls: {offenders}"


def test_no_hardcoded_home_paths():
    pattern = re.compile(r"/home/[\w.-]+/")
    offenders = []
    for p in REPO_ROOT.rglob("*"):
        if not p.is_file() or p.suffix not in {".ipynb", ".py", ".json", ".md"}:
            continue
        if any(part in SKIP_PARTS for part in p.parts):
            continue
        for m in pattern.finditer(p.read_text(encoding="utf-8")):
            offenders.append(f"{p.relative_to(REPO_ROOT)}: {m.group(0)}")
    assert not offenders, f"hardcoded /home/ paths: {offenders}"


def test_committed_notebooks_have_no_outputs():
    stale = []
    for p in iter_notebooks():
        nb = json.loads(p.read_text(encoding="utf-8"))
        for cell in nb.get("cells", []):
            if cell.get("cell_type") == "code" and (cell.get("outputs") or cell.get("execution_count") is not None):
                stale.append(str(p.relative_to(REPO_ROOT)))
                break
    assert not stale, f"notebooks with stale outputs (run scripts/clean_notebooks.py): {stale}"


def test_root_layout_contains_unified_files():
    for rel in ("README.md", "requirements.txt", ".gitignore", "scripts/clean_notebooks.py",
                "scripts/execute_notebooks.py", "scripts/verify_repo.py", "tests/conftest.py"):
        assert (REPO_ROOT / rel).is_file(), f"missing {rel}"
    for junk in ("convert_notebooks.py", "jupyter_cleanup_report.txt"):
        assert not (REPO_ROOT / junk).exists(), f"stale root file {junk} should be removed"


def test_tai_images_deduplicated():
    import hashlib

    images = [p for p in (REPO_ROOT / "TAI" / "images").iterdir() if p.is_file()]
    hashes = set()
    for p in images:
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        assert h not in hashes, f"duplicate image: {p.name}"
        hashes.add(h)
    assert len(images) == 39, f"expected 39 unique TAI images, found {len(images)}"
