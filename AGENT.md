# AGENT.md — Persistent Rules for APSD_TAI_LAB / Vault Sessions

This file is the single source of truth for every future agent session working on
this repository and its companion Obsidian vault. Read it fully before any edit.
`HANDOFF.md` (same location) records session-by-session progress and the exact
next issue to execute.

## 1. Repository topology

| Repo | Role | Branch |
| --- | --- | --- |
| `Vtheonly/APSD_TAI_LAB` | Code & labs: `APDS/` (data science), `TAI/` (image processing), `TAI/utils/`, `TAI/docs/`, `TAI/images/`, `tests/`, `scripts/` | `main` |
| `Vtheonly/UMBB-Master-1` | Obsidian vault: `Data Science/`, `Image Processing/` (formerly `TAI/`), `Libraries/`, `Quiz/` | `image-processing-data-science` |

- **Branch topology (post-consolidation, user directive):** the lab repository
  was consolidated into a SINGLE `main` branch (old `master` and
  `image-processing-data-science` branches deleted after verifying they were
  fully contained in `main`; default branch is `main`). ALL lab pushes now go
  to `main`. The vault repository keeps its subject branches — push ONLY to
  its `image-processing-data-science` branch; its `main` stays empty, and
  `networking`/`databases` are untouched. Never merge the two repositories.
- **Vault folder rename (from the consolidation):** the vault's `TAI/` track
  folder is now `Image Processing/` (the rename was done on the old `main`
  and merged into `image-processing-data-science`). Vault note paths in
  issues that say `TAI/09.x` etc. now live under `Image Processing/09.x`;
  wikilinks resolve by filename and were verified unaffected (0 broken).
- Keep the two clones side by side (this repo and the vault checkout of
  `UMBB-Master-1` branch `image-processing-data-science`). Push URLs embed the
  PAT (already configured); never write the PAT into any committed file.
- GitHub issues are tracked ONLY on `APSD_TAI_LAB` (via REST API — `gh` CLI is
  not installed). Vault changes are referenced in issues by vault-relative path.
- Work in **small, validated units**: at most 1–2 issues per session, then hand
  off. Commit and push incrementally after each validated unit.

## 2. Authoritative curriculum scope (STRICT)

The ONLY authoritative sources — never invent topics beyond them:

**APDS track (15 PDFs, IA2 - AP_DS - 2025/2026, M. BOUSTIL):**
Chapters 1–6 (Introduction PDS, Setup Python Env, Python Essentials parts 1–2,
Essential Python Libraries parts 1–2, Data Cleaning & Preprocessing, EDA) and
TP1–TP5 (incl. Tutorial 03 v2 "Exercise 6 — one million products", Tutorial 04
Exercises 01–04 + Project, Tutorial 05).

The APDS PDFs are not distributed in this repo (only the TP1 handout is
archived, at `APDS/docs/TP1_Chapter_Introduction.pdf`); the full set lives
in the user's private `Obsidian_Notes` repo (branch `main`) under
`Master 1/S1/Image Processing and Data Sceince/PDF LAB TD TP/Python Data
Science/` (`Cours/Chapter_1..6.pdf`, `TPs/TP1..TP5 + Project_1.pdf`;
TAI PDFs also there under `PDF LAB TD TP/TAI/`). Fetch with the PAT when a
session must verify an APDS fact against the originals.

**TAI track (in-repo `TAI/docs/`):**
- `assignments/tp1_enonce_fr.pdf`, `assignments/tp1_assignment_en.pdf`,
  `assignments/tp2_enonce_fr.pdf`
- `courses/tai_chap1_part1.pdf`, `courses/tai_chap1_part2.pdf`,
  `courses/tai_chap2_parts1_2_3.pdf`
- `references/getreuer_2009_contour_stencils.pdf`

Verified authoritative rulings (Session 1, do not re-litigate):
- **Nagao center clique = 3×3 square (9 pixels).** The figure in
  `tp2_enonce_fr.pdf` p.3 (decoded programmatically) shows 8 peripheral 7-pixel
  regions + a 3×3 centre; `TAI/utils/filters.py:build_nagao_masks` is correct.
  Course slide ~102 loosely says "9 fenêtres de 7 pixels" — treat the figure +
  code as canonical. Any vault note with a 5-pixel cross centre is wrong.
- **Contour Stencils = full Getreuer 2009, 12 oriented stencils, output
  `(2h, 2w)`.** `tp2_enonce_fr.pdf` Ex 6 points to the Getreuer article;
  `TAI/utils/super_res.py` implements it. The 2-diagonal `(2H-1, 2W-1)` toy in
  vault notes contradicts the lab and must be corrected (a simplified hand
  example may be kept only if clearly labelled as a pedagogical reduction of
  the 12-stencil rule).
- **Instructor PDF quirks must be documented, never silently "fixed":**
  TP4 Ex 3 thresholds `60,000` / `Satisfaction ≥ 8` vs actual data ranges
  (`TotalCost` 420–2610, `Satisfaction` 3.5–4.7); Ch5 `median_income` naming;
  `unidecode`-after-regex order; Titanic `name` column absent from
  `sns.load_dataset('titanic')`.

## 3. Unified 6-stage curriculum map (single learning path)

Organise ALL content — labs and vault — around six progressive stages; libraries
appear when a stage needs them (no standalone `Libraries/` syllabus):

1. **Stage 1 — DS lifecycle & environment:** Ch1–2, TP1–TP2, TAI `00_Environment`.
2. **Stage 2 — Core Python & streaming design:** Ch3 parts 1–2, TP3 Ex 1–6
   (1M patients AND 1M products), handwritten construction guide (`00.5`).
3. **Stage 3 — 2D/3D arrays, plots & digital images:** NumPy + Matplotlib core +
   OpenCV basics; APDS TP4 Ex 1–2, TAI TP1 Exo 2–5.
4. **Stage 4 — Tabular engineering, preprocessing & EDA:** Pandas, Seaborn,
   Sklearn prep, Plotly, Basemap; APDS Ch4–6, TP4 Ex 3–4 + Project, TP5, iris EDA.
5. **Stage 5 — Degradation, restoration & spatial/spectral filtering:** noise,
   PSNR/SSIM, convolution, integral image, adaptive mean, Bilateral/Nagao;
   TAI TP2 Exo 1–3, worked ex 10.1.
6. **Stage 6 — Contrast, morphology, segmentation & super-resolution:**
   HE/AHE/CLAHE, morphology/watershed/Zhang-Suen, Otsu/KMeans, Getreuer SR;
   TAI TP2 Exo 4–6, worked ex 10.2–10.4.

`00. Master Curriculum Roadmap.md` must express this 6-stage map (it currently
uses a 5-phase structure); `Libraries/00. Library Learning Roadmap.md` must be
retired as a competing syllabus and repurposed as a stage-indexed API lookup.

## 4. French TAI symbol & naming rules

Preserve the instructor's exact function/variable names in `TAI/` and vault
`Image Processing/09.*` notes (folder renamed from `TAI/` in the vault): `im1`, `imb1`, `seuillage_fixe_perso`, `calcul_histogramme_perso`,
`filtreMoyenne`, `filtreMedian`, `filtrebilateral`, `filtreNagao`,
`filtreMoyenneAdaptative`, `filtreMoyenne_separable`, `expansionHisto`,
`egalisationHistoGlobale`, `egalisationAHE`, `egalisationCLAHE`,
`super_resolution_bilineaire_2x`, `super_resolution_contour_stencils_2x`.
`TAI/utils/` is the canonical implementation; vault notes reference it, never
duplicate divergent code. Images load from `TAI/images/` via
`TAI.utils.env_io.bootstrap()`; outputs go to `TAI/outputs/` (never committed).

## 5. `.5` handwritten-exam standards (vault `Libraries/*.5.md`)

- Clean multiline Python: no semicolon-chained one-liners
  (`df.info(); df.isnull().sum()` is forbidden), explicit imports, 4-space
  indentation blocks.
- Structure: problem-to-code construction method (parse I/O → choose structure →
  initialize → pseudocode → write → hand-trace), trap matrices, THEN unsolved
  paper drills (trace tables, predict-output, fill-in-blanks, spot-the-bug,
  math-to-code, synthesis) with separated answer keys.
- No phantom references to `Computer Vision.md` (file does not exist — verified).
- Every drill answer must be executed in Python before being committed.

## 6. Validation commands (run before every push)

From the `APSD_TAI_LAB` clone (venv needs the contrib OpenCV build for
`cv2.ximgproc`; the headless variant works in sandboxes):

```bash
pip check                                            # 0 conflicts
python -m pytest -q                                  # 100% pass expected
MPLBACKEND=Agg python scripts/execute_notebooks.py   # 22/22 notebooks, 0 cell errors
python scripts/verify_repo.py                        # PASS
python scripts/check_wikilinks.py <path-to-vault-clone>   # 0 broken wikilinks
```

Vault-only sessions still run the wikilink check plus a Python execution pass of
any drill/answer code added to notes.

## 7. Session protocol

1. Read `AGENT.md` (this file), `HANDOFF.md`, and `gh issue list` equivalent
   (REST: `GET /repos/Vtheonly/APSD_TAI_LAB/issues?state=open`).
2. Pick the single next issue named in `HANDOFF.md`.
3. Read the relevant PDFs (`TAI/docs/`, APDS course PDFs) / code / notes BEFORE
   editing. If a fact is missing or ambiguous, do NOT guess: log it in
   `HANDOFF.md` and in a GitHub issue.
4. Implement only what is verified. Run the validation commands of section 6.
5. Close/annotate issues via REST API; update `HANDOFF.md` (completed work,
   verified findings, blockers, next issue # + continuation prompt); push BOTH
   repos; stop.
