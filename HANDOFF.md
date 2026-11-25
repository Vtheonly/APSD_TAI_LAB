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

## Session 2 — COMPLETE (issues #22, #5, #34: first fixes on BOTH repos)

**Completed work** (lab commit `388228e` + `01ac8d6`; vault commit `66098db`;
issues #22/#5/#34 closed with evidence comments):
1. **#22 — 4 TAI notebook bugs fixed** (lab): `dt_cv` now times
   `cv2.calcHist` (was a second Python-loop run); σ²=900 PSNR 15.6 → 18.59 dB
   (+ Gaussian formula note); SAT formula corrected to
   `SAT(b,r) - SAT(t,r) - SAT(b,l) + SAT(t,l)` (matches
   `filtreMoyenne_integrale`); misaligned crop/resize/rotate PSNR table in
   `03_geometric_and_draw_ops` replaced with valid checks (exact crop equality,
   lossless `rot90` — verified `cv2.ROTATE_90_CLOCKWISE == np.rot90(k=-1)` —
   im2 shape/aspect/DC conservation, aligned blur PSNR).
2. **#5 — APDS/01 TP2 gaps** (lab): new `plt.plot(df["Age"], df["Cholesterol"],
   marker="o")` cell (TP2 p. 2); README TP2 Steps 4–5 (git workflow +
   `pip freeze > requirements.txt`).
3. **#34 — Libraries/22 SSIM** (vault): `calculate_ssim_windowed` (global SSIM,
   misleading name) replaced by the canonical `calculate_ssim` — byte-identical
   to `TAI/utils/metrics.py` (11x11 Gaussian σ=1.5, Wang 2004, channel-wise,
   `data_range`); `calculate_psnr` `max_val`→`data_range`; windowing theory +
   global-shortcut warning added; cross-links to the canonical module.

**Validation:** `pytest -q` 176 passed · `execute_notebooks.py` 22/22, 0 cell
errors (run twice: after #22, and after #5's new cell) · `verify_repo.py` PASS ·
`pip check` clean · vault wikilinks 0 broken (1017 links) · Libraries/22 code
block extracted & executed, outputs equal `TAI/utils/metrics.py` exactly.

**New verified facts:**
- Notebooks are committed **output-free** (repo convention enforced by
  `test_notebooks_have_no_stale_outputs`); `execute_notebooks.py` executes to
  a temp dir and never writes back — edit sources only, keep outputs `[]`.
- APDS course/TP PDFs are **not in either repo**; the Phase-1 audit article
  (user-provided) is the working spec for APDS-side content. TAI side has the
  real PDFs in `TAI/docs/` — always prefer them.
- Working fix scripts live outside the repo, next to the clones (NOT committed —
  keeps `scripts/` free of one-off code; only durable tooling like
  `check_wikilinks.py` is committed).
- Post-issue comments via a small Python script (shell heredoc + JSON quoting
  mangles bodies; see `scripts/comment_issues_22_5.py` pattern).

## Session 3 — issue #2 (APDS/00_Introduction_Exercises, TP1)

**Completed work** (lab commit `1805a03`; issue #2 commented, left OPEN —
see blocker):
1. Created `APDS/00_Introduction_Exercises/` per the issue spec: `README.md`
   (with explicit source-status note) + `notebooks/01_introduction_exercises.ipynb`
   (13 cells, output-free, nbformat 4.5, standard Step-0 bootstrap).
   Contents: 8-step workflow reference cell; **Ex 1** five-slot answer schema
   (domain / data types / key steps) + completion guide; **Ex 2** verified
   heart-disease role mapping (Data Scientist, ML Engineer, Data Engineer,
   Domain Expert, BI Analyst — each tied to workflow steps) + 3
   critical-thinking Q&As inside verified scope.
2. `APDS/README.md`: index row 00 (nine projects).

**Validation:** `pytest -q` 176 passed · `execute_notebooks.py` **23/23**,
0 cell errors · `verify_repo.py` PASS · `pip check` clean.

**Key verified finding (affects all APDS-side issues):**
- `TP1_Chapter_Introduction.pdf` is in **neither repo**, none of the owner's
  92 GitHub repos (checked via REST: only `UMBB-A2I` and `UMBB-Master-1`
  match APDS/TAI keywords; UMBB-A2I holds no APDS PDFs), and the audit
  article transcribes only the exercise *structure*, not the five scenario
  domains or Ex 2's exact questions. The five Ex-1 domains are committed as
  `TO_CONFIRM_FROM_TP1_PDF` placeholders (issue #2 comment documents this).
  **Same risk applies to every APDS issue that needs exact PDF text** —
  where the article gives exact commands/values, implement them; where it
  gives only structure, scaffold + placeholder + issue comment.

## Session 4 — issues #4, #3, #6, #11, #7 (Stage 1+2 sweep, branch policy change)

**Branch policy change (user directive):** from this session on, ALL pushes
go ONLY to `image-processing-data-science` — never `master`/`main`. The lab
repo's `image-processing-data-science` branch was cut from master (`c318552`)
and pushed; AGENT.md §1 records the rule.

**Completed work** (5 issues; vault `97e31f4`, `d66640f`, `b91b919`; lab
`19e6dc8`, `cc531da` — all on `image-processing-data-science`):
1. **#4 — vault 01.3/01.4:** python.org-vs-Anaconda install section; 5th IDE
   (JupyterLab); main-DS-libraries table incl. Statsmodels/XGBoost/LightGBM;
   full Git workflow (init→push + day-to-day cycle). 01.4: stats corrected
   against the real CSV (mean age 46.2, chol 230, per-patient hypertensive
   rows), new TP2 Steps 4–5 section, CSV block byte-verified.
2. **#3 — vault 01.1 rename:** `01.1 ... CRISP-DM Workflow.md` → `01.1 ...
   8-Step Data Science Workflow.md` (git mv, 5 inbound links fixed); explicit
   "not CRISP-DM" callout; 8 steps rewritten course-scope (Docker/FastAPI/
   AUC-ROC demoted to supplementary); new sections: Skills, R/Julia, Python
   tools (PySpark/Dask/SQLAlchemy), Python overview, TP1 link. Quiz 01: 8
   CRISP-DM wordings replaced (semantics preserved), validator 237 ALL VALID.
3. **#6 — vault 02.*:** lambda/map/filter/sorted (02.4), strings+f-strings
   (02.1), list slicing/concat/repeat + `[[]]*3` trap (02.2), tuples + set
   methods with discard/remove trap (02.3), json/DictWriter/text-modes
   (02.10), class-vs-instance attrs + extended dunders + naming table (02.8).
   CPython internals demoted to supplementary callouts (02.1/02.2/02.3/02.6).
   Every snippet executed & asserted; wikilinks 1027, 0 broken.
4. **#11 — lab requirements:** `plotly>=5.18` + `unidecode>=1.3` added;
   README "Dependency Decisions" documents Basemap NOT installed (deprecated,
   Cartopy successor, GEOS/PROJ fragility). pip check clean; imports tested.
5. **#7 — lab APDS/03+04:** report.txt headers fixed (`Min average` etc.,
   notebook re-executed); APDS/04 Ex 6: `generate_large_products_csv`,
   `stream_products`, `total_inventory_value`, notebook §4 benchmark (asserts
   list-vs-generator totals equal), `run_products_benchmark`, 6 new tests.

**Validation:** pytest **182 passed** (176+6) · execute_notebooks **23/23,
0 errors** · verify_repo PASS · pip check clean · wikilinks 0 broken ·
quiz validator 237 questions ALL VALID · all added snippets executed.

**New verified facts / lessons:**
- Quiz validator takes explicit paths; `Quiz/00. Quiz Master Index.md` is an
  index (not a bank) and fails frontmatter checks by design — validate the
  `Quiz 0X` files themselves.
- Shell heredocs corrupt nested-quote Python (the Session 2 lesson recurred —
  one retry on the #7 tests); persisted scripts in the agent workspace
  `scripts/` folder (outside both repos) are the only reliable route for
  code with nested quotes. One such failed heredoc also died before writing
  `.gitignore` — always verify the intended side effect happened.
- `s.find("cie")` on `"  Data Science  "` is 8 (not 11) — snippet-execution
  verification caught the note's own comment error before commit.

## Remaining / blocked
- 26 issues open: #2 (awaiting TP1 handout text — placeholders committed),
  #8–#10, #12–#21, #23–#33, #35. Nothing blocked otherwise.
- Reminder for content sessions: the APDS-side issues rely on the article's
  transcription of the PDFs; keep implementations strictly within what the
  article + PDF-derived details state, and record any ambiguity as an issue
  comment rather than guessing.

## Next session

**Execute issue #8: "[stage-2][track-apds] APDS/02: processed-data step + Product.__str__ showcase in analysis.ipynb"** (next open in numeric order; small, well-scoped, pairs with the just-landed #7 streaming work).

Continuation prompt (paste as-is):

> You are continuing the APSD_TAI_LAB / Obsidian-vault curriculum work. Read
> `AGENT.md` and `HANDOFF.md` in the APSD_TAI_LAB clone (branch
> `image-processing-data-science` — ALL pushes go there only, never
> master/main), then execute GitHub issue #8 (APDS/02: add the
> data/processed/ workflow step and showcase `Product.__str__` in
> `notebooks/analysis.ipynb`, per Tutorial 03 / the Phase-1 audit article §6A;
> update the project README). Validate with `python -m pytest -q` (182
> passing expected), `MPLBACKEND=Agg python scripts/execute_notebooks.py`
> (23/23, 0 cell errors), `python scripts/verify_repo.py` (PASS). Then close
> issue #8 via the REST API with an evidence comment, update `HANDOFF.md`
> (session record + next issue), commit and push to
> `image-processing-data-science` only, and stop. If #8 is already done, take
> the next open issue in numeric order (#9, then #10, then #12+).

Recommended ordering after #8: #9 (03.1 bridge) → #10 (03.5/10.5) → #12
(Plotly/Basemap notes) — the Stage 3/4 vault cluster; then #13–#19 (Stage 4
APDS labs) and #23–#29 (TAI sync + bug clusters). Keep 1–2 issues per
session unless they are as small as #11.

