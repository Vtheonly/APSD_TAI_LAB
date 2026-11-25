# HANDOFF.md — Session Log & Next Steps

Companion to `AGENT.md` (read that first). Every session appends its record here
and updates the "Next session" block at the end.

## Session 1 (Setup Pass) — COMPLETE

**Goal:** verify the seed list against the real repositories, create `AGENT.md`,
open structured GitHub issues, establish the validation baseline, fix the
baseline hygiene failures. No curriculum content edits.

### Completed work
1. Cloned both repos (`APSD_TAI_LAB` @ main; `UMBB-Master-1` @
   `image-processing-data-science`); PAT wired into push URLs only.
2. Read all 7 `TAI/docs/` PDFs (pdftotext) — they exist and are complete
   (assignments tp1_enonce_fr, tp1_assignment_en, tp2_enonce_fr; courses
   tai_chap1_part1/part2, tai_chap2_parts1_2_3; getreuer_2009 reference).
3. Created `AGENT.md` (persistent rules) and `scripts/check_wikilinks.py`
   (vault link checker, committed into the repo).
4. Opened 35 GitHub issues (#1–#35), each labeled by stage/track, covering every
   verified gap from the seed list + newly found defects.
5. **Fixed issue #1 (hygiene):** deleted the 22 stale `.txt` notebook dumps and
   `scripts/convert_notebooks.py` (both introduced by commit `9ff2e9c`),
   switched `.gitignore` to keep `TAI/outputs/.gitkeep` tracked.
6. Validation after fix: `pytest -q` **176 passed / 0 failed**;
   `scripts/verify_repo.py` **PASS**; `pip check` clean; wikilinks **0 broken**;
   `execute_notebooks.py` 22/22 (pre- and post-fix).
7. Environment note: sandbox OpenCV replaced with `opencv-contrib-python-headless`
   (5.1.0) so `cv2.ximgproc` is available — this satisfied `verify_repo.py`.

### Verified findings (evidence log)
- **All Phase-1 "missing" items exist:** `TAI/docs/` (7 PDFs), `TAI/images/`
  (39 files, SHA-deduplicated), `tests/` (10 files), `scripts/` (4), the three
  CSVs (`patients.csv` 10 rows; `hospital_original.csv` 8 rows, schema
  City/Department/Age/DaysAdmitted/DailyCost/Satisfaction/Readmitted;
  `messy_medical.csv` 10 rows with real missingness/dirty values).
- **Vault was restructured since the Phase 1 audit:** `Image Processing/` is now
  `TAI/`, and `Quiz/` **exists** (21 quiz files + master index + validator) —
  the audit's "missing Quiz" is obsolete; wikilink check reports **0 broken**.
- **`Computer Vision.md` does NOT exist**; it is referenced as plain backtick
  text (not wikilinks) in 11 files — cosmetic phantom references (issue #33).
- **Nagao centre clique = 3x3 square (9 px):** figure on p. 3 of
  `tp2_enonce_fr.pdf` decoded programmatically (8 peripheral 7-px regions +
  3x3 centre). `TAI/utils/filters.py:build_nagao_masks` is correct; vault
  `02.6`, `09.5`, `Libraries/20`, `26` teach a 5-px cross (issue #23).
- **Contour Stencils = full Getreuer 2009, 12 stencils, (2h, 2w):** `tp2_enonce_fr.pdf`
  Ex 6 defers to the Getreuer article; `TAI/utils/super_res.py` implements it.
  Vault `24/24.5` teach a 2-diagonal `(2H-1, 2W-1)` toy and even assert "never
  (2H, 2W)" — wrong for the lab (issue #25).
- **All 4 TAI notebook bugs reproduced** (dt_cv double-loop timing; σ²=900 →
  "15.6 dB" vs computed 18.59 dB; SAT formula duplicated `+SAT(b+r)`;
  misaligned crop/resize PSNR) — issue #22.
- **APDS gaps reproduced:** no `APDS/00` (TP1); `patients_analysis.ipynb` has
  no `plt.plot`; no 1M-products streaming; `06/02` titled "Exercise 04";
  `report.txt` uses `Min_average`-style headers; `07` has no quarterly totals /
  best-month annotation / conclusions; `08/01` has zero `sns.` calls; no
  `APDS/09` EDA notebook; `requirements.txt` lacks `plotly`/`unidecode`.
- **Vault gaps reproduced:** 03.1 is a 24-line stub; CRISP-DM in 01.1
  (filename + 5 mentions); 0 `lambda` mentions in all of `02.*`; 0
  `json.dump`/`DictWriter`; 0 `unidecode`; 0 `plotly`; `10.5` has 0 Seaborn
  API coverage; `23.5` has ~0 Sklearn coverage; Master Roadmap is 5-phase;
  `Libraries/00` is a standalone competing syllabus; Bilateral 3-4x and Nagao
  4x duplicated.
- **Open questions (kept open, not guessed):** none blocking — the Phase 1
  "unknowns" (TAI/docs, CSVs, Quiz, Computer Vision.md) all resolved as above.
  `basemap` installability remains a documented decision (issue #11: teach
  conceptually, do not add to requirements).

### Issue map (35 open at end of Session 1)
- #1 hygiene (CLOSED this session) · #2–#5 Stage 1 · #6–#8 Stage 2
- #9–#12 Stage 3/4 libraries · #13–#21 Stage 4 APDS labs + vault 04/05
- #22 TAI bug fixes · #23 Nagao · #24 Bilateral · #25 Contour Stencils
- #26–#29 vault 09.x sync · #30–#33 .5 exam prep · #34 Libraries/22 SSIM
- #35 roadmap unification

## Remaining / blocked
- Nothing blocked. All 34 content issues (#2–#35) are ready to execute in the
  order below. Network-dependent steps (e.g. `sns.load_dataset('titanic'/'iris'`
  in issues #18/#19) should be attempted and, if offline, documented with a
  local-data fallback per issue text.

## Next session

**Execute issue #2: "[stage-1][track-apds] Create APDS/00_Introduction_Exercises (TP1 Ex 1-2)".**

Continuation prompt (paste as-is):

> You are continuing the APSD_TAI_LAB / Obsidian-vault curriculum work. Read
> `AGENT.md` and `HANDOFF.md` in the APSD_TAI_LAB clone, then execute GitHub
> issue #2 (create `APDS/00_Introduction_Exercises` implementing
> `TP1_Chapter_Introduction` Exercises 1–2: README + notebook with the standard
> Step-0 bootstrap cell; update `APDS/README.md`). Source of truth: the TP1 PDF
> (Chapter 1 introduction course context) — do not invent scenarios beyond the
> five named domains. Validate with `python -m pytest -q` (100% pass),
> `MPLBACKEND=Agg python scripts/execute_notebooks.py` (23/23 notebooks),
> `python scripts/verify_repo.py` (PASS). Then close issue #2 via the GitHub
> REST API with a summary of changed files and test results, update
> `HANDOFF.md` (session record + next issue), commit and push, and stop.
> If #2 is already done, take the next open issue in numeric order.

Recommended ordering after #2: #5 → #4 → #3 (Stage 1 batch), then #22 (small,
high-value TAI bug fixes), then Stage 2 batch (#6, #7, #8), etc. Prefer
finishing a stage's APDS+vault issues together so cross-references land in one
push.
