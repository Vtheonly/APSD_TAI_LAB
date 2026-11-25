# TAI — Traitement et Analyse d'Images (Image Processing & Analysis Labs)

This folder contains the complete **TAI coursework track** (TP1 & TP2 practical
labs), unified into a single clean hierarchy that mirrors the `APDS/` numbered
project paradigm. All notebooks are written in **English** (with the required
French exercise symbol/function names preserved, e.g. `im1`, `imb1`,
`sp_noise`, `filtreMoyenne`, `filtreNagao`, `expansionHisto`,
`egalisationCLAHE`, `super_resolution_bilineaire_2x`), and every lab follows
the same structure:

1. **Assignment Objectives**
2. **Step 0 — Portable bootstrap** (local IDE/Jupyter + Google Colab)
3. **Mathematical Principles & Intuition** (LaTeX: the *what* and the *why*)
4. **Implementation** (OpenCV reference **and** from-scratch verification)
5. **Quantitative verification tables** (bit-for-bit equality, max pixel
   difference, PSNR/SSIM, runtimes)
6. **Inline Matplotlib visualizations** (never `cv2.imshow`)
7. **Analysis & Key Takeaways**

## Directory Layout

```
TAI/
├── README.md                              # this file
├── images/                                # THE single deduplicated image dataset (39 files)
├── utils/                                 # shared Python package (single source of truth)
│   ├── __init__.py
│   ├── env_io.py                          # Colab/local detection, root discovery, load_image,
│   │                                      #   show_images, plot_image_with_hist
│   ├── metrics.py                         # calculate_psnr, calculate_ssim (unified conventions)
│   ├── noise.py                           # add_gaussian_noise, sp_noise (deterministic seeds)
│   ├── basics.py                          # seuillage_fixe_perso, calcul_histogramme_perso
│   ├── filters.py                         # filtreMoyenne (+separable/integral), filtreMedian,
│   │                                      #   filtrebilateral, filtreMoyenneAdaptative, filtreNagao
│   ├── morphology.py                      # custom_erode/dilate/opening/closing, Zhang-Suen thinning
│   ├── contrast.py                        # expansionHisto, egalisationHistoGlobale/AHE/CLAHE
│   └── super_res.py                       # super_resolution_bilineaire_2x, contour stencils 2x
├── 00_Environment_and_NumPy_Foundations/
│   ├── notebooks/01_environment_setup.ipynb   # toolchain + repository validation (TP1 Exo1, extended)
│   └── scripts/numpy_slicing_foundations.py   # chained vs. tuple indexing demo (from TAI 2)
├── 01_TP1_Image_Fundamentals/
│   └── notebooks/
│       ├── 01_image_manipulation.ipynb        # TP1 Exo2 — BGR/grayscale, pixels, drawing
│       ├── 02_fixed_thresholding.ipynb        # TP1 Exo3 — fixed threshold T=80
│       ├── 03_geometric_and_draw_ops.ipynb    # TP1 Exo4 — resize, crop, rotate, blur
│       └── 04_image_histograms.ipynb          # TP1 Exo5 — grayscale & colour histograms
├── 02_TP2_Noise_and_Spatial_Filtering/
│   └── notebooks/
│       ├── 01_image_noise.ipynb               # TP2 Exo1 — Gaussian & salt-and-pepper noise
│       ├── 02_spatial_filtering_and_psnr.ipynb# TP2 Exo2 — mean/median/bilateral + PSNR
│       │                                      #   + graded work (a) separable/integral mean,
│       │                                      #   (b) adaptive & MMSE filters
│       └── 03_nagao_adaptive_filter.ipynb     # TP2 Exo3 — Nagao edge-preserving filter
├── 03_TP2_Morphology_and_Contrast/
│   └── notebooks/
│       ├── 01_mathematical_morphology.ipynb   # TP2 Exo4 — erosion/dilation/open/closing,
│       │                                      #   cell counting (watershed) & Zhang-Suen
│       └── 02_histogram_and_contrast.ipynb    # TP2 Exo5 — expansion, global/AHE/CLAHE
├── 04_TP2_Super_Resolution/
│   └── notebooks/
│       └── 01_super_resolution_contour_stencils.ipynb  # TP2 Exo6 — interpolation benchmark +
│                                                       #   Getreuer 2009 contour stencils
├── docs/                                  # consolidated unique PDFs
│   ├── assignments/                       # tp1_enonce_fr, tp1_assignment_en, tp2_enonce_fr
│   ├── courses/                           # tai_chap1_part1/2, tai_chap2_parts1_2_3
│   └── references/                        # getreuer_2009_contour_stencils
└── outputs/                               # runtime generated images (git-ignored, never committed)
```

## Consolidated Image Dataset (`TAI/images/`)

All TP1/TP2 images were merged into **one** SHA-256 deduplicated folder (39
unique files — no duplicates, nothing lost). Mapping from the original course
filenames:

| Original file | Unified name in `TAI/images/` |
|---|---|
| `Images/BoatsColor.bmp` | `tp1_exo2_boats_color.bmp` |
| `Images/pepper.bmp` | `tp1_exo4_exo5_peppers_color.bmp` |
| `Images/cameraman.bmp` | `tp1_tp2_cameraman_gray.bmp` |
| `Images/compteur.jpg` | `tp1_tp2_compteur_water_meter.jpg` |
| `Images/airplane.bmp` | `tp1_tp2_sample_airplane_f16.bmp` |
| `Images/baboon.bmp` | `tp1_tp2_sample_baboon_mandrill.bmp` |
| `Images/barbara.bmp` | `tp1_tp2_sample_barbara_portrait.bmp` |
| `Images/blobs.bmp` | `tp1_tp2_sample_binary_blobs.bmp` |
| `Images/bateau.jpg` | `tp1_tp2_sample_boat_sailboats.jpg` |
| `Images/boats.bmp` | `tp1_tp2_sample_boats_harbor_gray.bmp` |
| `Images/bridge.bmp` | `tp1_tp2_sample_bridge_landscape.bmp` |
| `Images/cablecar.bmp` | `tp1_tp2_sample_cablecar_mountain.bmp` |
| `Images/clown.bmp` | `tp1_tp2_sample_clown_portrait.bmp` |
| `Images/pens.bmp` | `tp1_tp2_sample_colored_pens.bmp` |
| `Images/Earth.bmp` | `tp1_tp2_sample_earth_globe.bmp` |
| `Images/finger.pgm` | `tp1_tp2_sample_fingerprint_1.pgm` |
| `Images/fingerprint1.pgm` | `tp1_tp2_sample_fingerprint_2.pgm` |
| `Images/flower.bmp` | `tp1_tp2_sample_flower_close_up.bmp` |
| `Images/fruits.bmp` | `tp1_tp2_sample_fruits_still_life.bmp` |
| `Images/girl.bmp` | `tp1_tp2_sample_girl_portrait.bmp` |
| `Images/goldhill.bmp` | `tp1_tp2_sample_goldhill_village.bmp` |
| `Images/houses.bmp` | `tp1_tp2_sample_houses_street.bmp` |
| `Images/kiel.bmp` | `tp1_tp2_sample_kiel_aerial.bmp` |
| `Images/lenna.bmp` | `tp1_tp2_sample_lenna_portrait.bmp` |
| `Images/lighthouse.bmp` | `tp1_tp2_sample_lighthouse_coast.bmp` |
| `Images/bone_scint.pgm` | `tp1_tp2_sample_medical_bone_scintigraphy.pgm` |
| `Images/Brain1.pgm` | `tp1_tp2_sample_medical_brain_mri_1.pgm` |
| `Images/Brain2.pgm` | `tp1_tp2_sample_medical_brain_mri_2.pgm` |
| `Images/Brain3.pgm` | `tp1_tp2_sample_medical_brain_mri_3.pgm` |
| `Images/ultrasound.pgm` | `tp1_tp2_sample_medical_ultrasound.pgm` |
| `Images/monarch.bmp` | `tp1_tp2_sample_monarch_butterfly.bmp` |
| `Images/Saturn.bmp` | `tp1_tp2_sample_saturn_planet.bmp` |
| `Images/soccer.bmp` | `tp1_tp2_sample_soccer_match.bmp` |
| `Images/brickwall.bmp` | `tp1_tp2_sample_texture_brickwall.bmp` |
| `Images/textureB.bmp` | `tp1_tp2_sample_texture_pattern.bmp` |
| `Images/yacht.bmp` | `tp1_tp2_sample_yacht_sea.bmp` |
| `Images/Zoneplate.png` | `tp1_tp2_sample_zoneplate_test_pattern.png` |
| `TAI_globules_rouges.jpg` | `tp2_exo4_globules_rouges_cells.jpg` |
| `TAI_TP2_glaucome.jpg` | `tp2_exo5_glaucoma_retinal_fundus.jpg` |

Generated outputs (e.g. `tp1_exo3_compteur_binary_imgb1.jpg`,
`tp2_exo1_cameraman_*.bmp`, `tp2_exo4_counted_cells.png`) are written to
`TAI/outputs/` at runtime and are **never** committed.

## `TAI/utils/` — Shared Algorithms

The from-scratch implementations live in `TAI/utils/` so that each algorithm
exists **exactly once** (no copy-pasted 45-line bootstrap blocks, no duplicated
`calculate_psnr` variants). The notebooks import them and still explain every
equation; `pytest` (see `tests/` at the repository root) verifies each one
against its OpenCV/NumPy reference, including bit-for-bit equality for:

- `seuillage_fixe_perso` vs `cv2.threshold`
- `calcul_histogramme_perso` vs `cv2.calcHist`
- `custom_erode` / `custom_dilate` / `custom_opening` / `custom_closing` vs
  `cv2.erode` / `cv2.dilate` / `cv2.morphologyEx` (neutral border padding +
  kernel reflection)
- `egalisationHistoGlobale` vs `cv2.equalizeHist`, `expansionHisto` vs
  `cv2.normalize`

Unified conventions documented in the modules:

- **PSNR** returns `float("inf")` when `MSE == 0` (the mathematically correct
  limit — replaces the old inconsistent `inf` / `100.0` mix).
- **Noise generators** are seeded (`seed=42` default) so `TP2_Exo1`, `Exo2`
  and `Exo3` share bit-identical noisy inputs.
- **No GUI calls**: every visualization goes through inline Matplotlib.

## Running the Labs

Every notebook starts with a **Step-0 bootstrap cell** that:

- works locally from any working directory (VS Code, PyCharm, JupyterLab,
  Jupyter, CLI `nbconvert`) by walking up to the repository root, and
- works on **Google Colab** — cloning the repository automatically when a
  notebook is opened directly from GitHub.

See the repository root `README.md` for environment setup (one `.venv`, one
`requirements.txt` — `opencv-contrib-python` is required for
`cv2.ximgproc.thinning`).
