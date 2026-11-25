# APSD_TAI_LAB

A unified workspace for two university coursework tracks — **APDS** (Advanced
Python & Data Science) and **TAI** (Image Processing & Analysis) — with one
virtual environment, one dependency file, one ignore file and one consistent
project paradigm.

```
APSD_TAI_LAB/
├── APDS/            # 8 numbered data-science projects (see APDS/README.md)
├── TAI/             # TP1 & TP2 image-processing labs (see TAI/README.md)
├── tests/           # pytest suite covering both tracks
├── scripts/         # repository helper scripts
├── requirements.txt # THE unified dependency file (both tracks)
├── .gitignore       # THE unified ignore file
└── README.md
```

- `APDS/` and `TAI/` are two distinct coursework tracks — they never share code
  but share the same environment and conventions.
- Everything a notebook needs (images, shared algorithms, data) is resolved
  from the repository root, so **every notebook runs from any working
  directory and on Google Colab** (see *Compatibility* below).

## Quick Start (Local)

```bash
git clone https://github.com/Vtheonly/APSD_TAI_LAB.git
cd APSD_TAI_LAB

# 1) create the single unified virtual environment
python -m venv .venv
source .venv/bin/activate          # Linux / macOS
# .venv\Scripts\activate           # Windows

# 2) install everything (both tracks, incl. opencv-contrib-python)
pip install -r requirements.txt

# 3) sanity checks
pip check                                   # 0 broken requirements
python -c "import cv2; print(hasattr(cv2, 'ximgproc'))"   # must print True
```

Then open any notebook with VS Code / PyCharm / JupyterLab / Jupyter
(`jupyter lab`) — select the `.venv` kernel and run top-to-bottom.

> **Important:** the environment must use `opencv-contrib-python` (installed
> by `requirements.txt`), *not* bare `opencv-python` — only the contrib build
> provides `cv2.ximgproc` (e.g. `cv2.ximgproc.thinning` for Zhang-Suen
> skeletonization in `TAI/03_TP2_Morphology_and_Contrast`).

## Google Colab

Two supported workflows — the Step-0 cell at the top of every notebook handles
both automatically:

1. **Open a notebook directly from GitHub** (File → Open notebook → GitHub, or
   the `Open in Colab` badge workflow): the first cell detects Colab, clones
   this repository into `/content/APSD_TAI_LAB`, installs
   `opencv-contrib-python` if `cv2.ximgproc` is missing, and adds the
   repository to `sys.path`.
2. **Clone first** (`!git clone https://github.com/Vtheonly/APSD_TAI_LAB.git`
   in a code cell, then open notebooks from the Files pane): same bootstrap
   detects the existing clone (also works from a mounted Google Drive folder
   named `APSD_TAI_LAB`).

No manual uploads of `TAI/images/` or `TAI/utils/` are ever needed.

## Repository Layout

### APDS — Advanced Python and Data Science (8 projects)

1. `01_Hospital_Data_Setup` — environment validation & first ingestion
2. `02_Sales_Inventory_Pipeline` — modular parsing & OOP valuation
3. `03_Student_Simulation_Analytics` — seeded synthetic cohort analytics
4. `04_One_Million_Record_Streaming` — memory profiling & generator streaming
5. `05_NumPy_Scientific_Computing` — NumPy aggregation & masking
6. `06_Hospital_Department_Analytics` — pandas indexing, risk scoring, pivots
7. `07_Monthly_Sales_Forecasting` — time series & visualization
8. `08_Data_Preprocessing_and_Modeling` — cleaning & scikit-learn pipelines

Each project has its own `README.md`; see `APDS/README.md` for the overview.

### TAI — Image Processing & Analysis (TP1 & TP2)

```
TAI/
├── images/                              # single SHA-256 deduplicated dataset (39 images)
├── utils/                               # shared algorithms (env_io, metrics, noise, basics,
│                                        #   filters, morphology, contrast, super_res)
├── 00_Environment_and_NumPy_Foundations/ # toolchain check + NumPy slicing foundations
├── 01_TP1_Image_Fundamentals/            # TP1 Exo2-5
├── 02_TP2_Noise_and_Spatial_Filtering/   # TP2 Exo1-3 (+ graded work a & b)
├── 03_TP2_Morphology_and_Contrast/       # TP2 Exo4-5 (morphology master solution)
├── 04_TP2_Super_Resolution/              # TP2 Exo6 (Getreuer 2009 contour stencils)
├── docs/                                # assignments / courses / references (unique PDFs)
└── outputs/                             # runtime generated images (git-ignored)
```

See `TAI/README.md` for the full lab map, the image-name mapping table and
the shared `TAI/utils` conventions.

## Compatibility (why every notebook "just works")

Every notebook — in both tracks — begins with a **Step-0 bootstrap cell** that:

- **Local (VS Code, PyCharm, JupyterLab, Jupyter, CLI `nbconvert`)**: walks
  upward from the current working directory to the repository root (marker:
  `README.md` + `APDS/` + `TAI/`) and resolves every path from it — the launch
  directory does not matter.
- **Google Colab**: clones the repository on demand and installs
  `opencv-contrib-python` only if `cv2.ximgproc` is unavailable.
- **No blocking GUI**: zero `cv2.imshow` / `cv2.waitKey` / `input()` calls —
  all visualization is inline Matplotlib.
- **No hardcoded absolute paths** anywhere.
- **Deterministic**: seeded noise generators and dataset generators make
  every figure/statistic reproducible.

## Testing & Verification

```bash
source .venv/bin/activate

pytest -q                        # full unit/integration suite (176 tests)
python scripts/execute_notebooks.py   # headless execution of 100% of notebooks
python scripts/verify_repo.py         # hygiene + SHA-256 integrity checks
python scripts/clean_notebooks.py     # strip outputs before committing
```

What each check covers:

| Check | Content |
|---|---|
| `tests/test_tai_env_io.py` | root resolution from arbitrary CWDs, `load_image` |
| `tests/test_tai_metrics.py` | `calculate_psnr`/`calculate_ssim` (incl. vs `cv2.PSNR`) |
| `tests/test_tai_noise.py` | deterministic `add_gaussian_noise` / `sp_noise` |
| `tests/test_tai_basics.py` | `seuillage_fixe_perso` == `cv2.threshold`, `calcul_histogramme_perso` == `cv2.calcHist` |
| `tests/test_tai_filters.py` | mean/separable/integral/median/bilateral/adaptive/Nagao filters |
| `tests/test_tai_morphology.py` | erode/dilate/open/close **bit-for-bit** vs OpenCV, Zhang-Suen thinning |
| `tests/test_tai_contrast.py` | expansion == `cv2.normalize`, global equalization == `cv2.equalizeHist`, AHE/CLAHE |
| `tests/test_tai_super_res.py` | bilinear 2x vs `INTER_LINEAR`, contour-stencil dimensions/ranges |
| `tests/test_apds_modules.py` | sales pipeline, students, dataset generator, streaming, sales utils |
| `tests/test_repo_hygiene.py` | no `.ipynb_checkpoints`, no `Untitled*`, no GUI calls, deduplicated images |
| `scripts/execute_notebooks.py` | `jupyter nbconvert --execute` on every notebook (MPLBACKEND=Agg) |
| `scripts/verify_repo.py` | static hygiene + SHA-256 dedup/integrity of `TAI/images/` |

## Repository Hygiene Rules

- One `.venv/` at the root, one `requirements.txt`, one `.gitignore` — no
  per-project duplicates.
- Generated artifacts (`TAI/outputs/`, `large_patients.csv`,
  `APDS/07/data/`) are git-ignored; committed notebooks carry **no outputs**
  (`scripts/clean_notebooks.py` enforces this before committing).
- `TAI/images/` is the single deduplicated image dataset; runtime outputs
  never pollute it.

## Git

This workspace is maintained as **one** Git repository; `APDS/` and `TAI/`
are organizational directories, not independent repositories.
