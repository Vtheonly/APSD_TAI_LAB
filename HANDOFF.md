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

## Session 5 — issue #8 (APDS/02 processed-data step + Product.__str__)

**Completed work** (lab commit `2535dff`, branch `image-processing-data-science`;
issue #8 closed with evidence comment):
1. `utils/helpers.py` + `utils/__init__.py`: new `save_processed_data(records,
   processed_dir)` — writes `data/processed/cleaned_data.txt` (cleaned
   `name,price,quantity` lines) and `products_summary.csv` (records +
   computed `total_value` column); exported from the package.
2. `scripts/create_products.py`: CLI creates `data/processed/` and persists
   both artifacts before the valuation report (smoke-run verified: corrupted
   row still skipped with warning, 5 valid products, Total 8500.0).
3. `notebooks/analysis.ipynb`: 11 → 15 cells — new **Section 5
   `Product.__str__` showcase** (`print(p)` / `str(p)` / f-string all yield
   the same line; contrast with a `__str__`-less class's default
   `<__main__.WithoutStr object at 0x...>` repr; assert `str(p)` equals the
   f-string rebuilt from the same fields) and **Section 6 processed-data
   step** (`save_processed_data` + CSV read-back round-trip assert vs the
   in-memory `Product`s). Executed outputs inspected: both cells print their
   OK lines; notebook stays output-free in the repo.
4. `.gitignore` + `data/processed/.gitkeep`: processed artifacts gitignored
   (generated data — same convention as `TAI/outputs/`), folder tracked.
5. `README.md`: documents the step, both artifacts, and the ignore choice.
6. `tests/test_apds_modules.py`: `TestSaveProcessedData` — 6 tests (txt+csv
   write, CSV header & total_value values, round-trip vs `Product`, empty
   records, missing dir → `FileNotFoundError`, overwrite semantics).

**Validation:** pytest **188 passed** (182+6) · execute_notebooks **23/23,
0 cell errors** · verify_repo PASS · pip check clean · wikilinks 0 broken
(1027) · CLI smoke run verified artifacts + gitignore behaviour.

**Session note:** fresh sandbox — both repos re-cloned; master clone was
behind (Sessions 1–3 only), the working branch `image-processing-data-science`
carries Sessions 4+ history. Sandbox env rebuilt: `opencv-contrib-python-
headless` 5.1.0 (ximgproc True) + `unidecode` installed; `pip check` clean.

## Session 6 — issues #9, #10, #12-#19 + remote re-clone verification (user directive: "Do 10 whole issues")

**User directive (this session):** complete 10 whole issues in one session — #9, #10, #12-#19 — overriding the
1-2 issues default of `AGENT.md`. The default itself is unchanged. The directive was completed: #15-#19 were implemented, sealed and closed in the
same session (see "Completed this session" below); #2 stays blocked as beforelied".

**Completed work**
- #9 (vault `b04083f`): `03.1` expanded from a stub into the NumPy / Pandas / Matplotlib bridge note (346 lines).
- #10 (vault `d99bd5e`): `Libraries/03.5` (562 lines) and `Libraries/10.5` (566 lines) rewritten — Chapter 4 Part 2
  coverage, Stage 3A (data plots) separated from Stage 3B (image rendering), 8 drills each with an executed key.
  The commit message swaps the two line counts (cosmetic). Scope notes left on #31 and #32.
- #12 (vault `5a8980a`): new `Libraries/10.6. Plotly Express and Basemap - Interactive and Geographic Figures`
  (389 lines, 14/14 python blocks executed) + links from both roadmaps, `10.5`, `03.5`, `03.1`.
- #13, #14: see the lab commits below; each was sealed by
  `scripts/seal_issue.py` (validation -> commit -> push -> close with the real outputs as evidence).

Lab commits since the Session 5 handoff:
  - `7302fef APDS/06/02: retitle Ex 03 Part 2, Tasks 3/4/5/9/10, handout-threshold scale quirk (#14)`
  - `7c407e8 APDS/05/02: Task 1 mean_per_student + 3 Extra Practice tasks, >= 15 vs > 15 boundary (#13)`
Vault commits since Session 4:
  - `5a8980a Libraries/10.6: Plotly Express (executed) + Basemap (conceptual); links from roadmaps, 10.5, 03.5, 03.1 (#12)`
  - `d99bd5e Libraries/03.5 + 10.5: Chapter 4 Part 2 coverage with Stage 3A/3B separation and drills (#10)`
  - `b04083f 03.1: expand the stub into the NumPy/Pandas/Matplotlib bridge note (#9)`

**Validation**
- End-of-session lab run: not re-run as a whole suite in this pass (sandbox time budget); the per-issue seals are the evidence.
- Vault wikilinks: notes indexed: 163  wikilinks checked: 1095 | BROKEN WIKILINKS: 0.
- Per-issue evidence: the closing comment of each issue (pytest, notebook execution, `verify_repo`, lint).

**New verified facts / lessons (Session 6)**
- Plotly 6.5.2: `px.bar` / `px.scatter` / `px.line` return one trace (`bar` / `scatter`; line mode `lines` or
  `lines+markers`); `hover_data` fills `trace.customdata` and extends `hovertemplate` with `%{customdata[i]}`;
  no `data_frame` -> ValueError; `ax=`, `hoverdata=`, `marker=` -> TypeError; `fig.set_title` / `fig.savefig` ->
  AttributeError; `update_layout(titel=)` -> ValueError; `px.bar(df, x=)` without `y` counts rows (y title `count`);
  string categories keep their order of appearance; `write_html` = 4,847,253 bytes vs `include_plotlyjs="cdn"`
  = 8,442 bytes; `to_image` raises `RuntimeError: Kaleido requires Google Chrome to be installed`.
- Basemap is NOT installed and cartopy is NOT installed; nothing was added. Basemap API signatures were taken
  from `matplotlib.org/basemap/stable/api/basemap_api.html` (release 2.0.0). Upstream today: the GitHub README
  carries no deprecation sentence, PyPI lists `basemap` 2.0.0 (numpy, matplotlib, pyproj, pyshp, basemap-data).
  The deprecation is the COURSE's position (Chapter 4 Part 2, p. 20, per the audit transcription) — say so.
- City coordinates used in 10.6 come from the Open-Meteo geocoding API (Algiers 36.73 N 3.09 E, Oran 35.70 N
  0.64 W, Annaba 36.90 N 7.77 E).
- Lesson: a file size measured on one figure is not valid for another — the first table quoted ~10 kB for a PNG
  that is 31,194 bytes on the 12-month series. Read the block output before writing the number.
- Lesson: `fig.show()` returns at once in this sandbox (no browser), so executed vault blocks may keep it.
- Tracker gap: no open issue covers syncing the vault tutorials `03.2`-`03.5` with the updated `APDS/05`-`07`
  notebooks (column names, `>= 15` vs `> 15`). Open an issue or fold it into #20+.
- `03.1` Section 8 maps Exercise 04 to `APDS/06/notebooks/03_hospital_matplotlib_vs_seaborn.ipynb`, which only
  exists once #15 is done.

**Helpers (outside the repos, in the session scripts folder)**: `nbedit.py` (output-free notebook editing),
`seal_issue.py` (validate -> commit -> push to `image-processing-data-science` -> close with evidence; placeholders
in `work/close_N.md`), `vault_lint.py`, `check_anchors.py`, `vault_exec.py`, `gh.py`, `verify_plotly_claims*.py`.
If the scripts are gone, the continuation prompt below describes each step without them.

**Completed this session (all sealed with evidence and closed)**
- `issue15_gen.py` - APPLIED: APDS/06/03 Exercise 04 notebook (9 audited charts) + HANDOFF path scrub -> 5c912bd (#15)
- `issue16_gen.py` - APPLIED: APDS/07 quarterly totals, printed insights, best-month annotation, alias table, 3 conclusions -> de5bfc1 (#16)
- `issue17_gen.py` - APPLIED: APDS/08/01 four TP5 Ex01 Task 2 charts (pixel-audited) + cap-vs-remove discussion -> 19245b0 (#17)
- `issue18_gen.py` - APPLIED: APDS/08/02 titanic EDA, name-column quirk, skew, scaled-vs-unscaled, confusion matrices, justification -> 0efca31 (#18)
- `issue19_gen.py` - APPLIED: new APDS/09 iris EDA project (README + notebook + index row 09) -> 4ec01df (#19)
- Remote verified by fresh re-clone mid-session: lab branch tip and vault tip byte-identical to the local clones;
  only untracked runtime artifacts differ (data/, __pycache__, TAI/outputs).
- Environment repaired mid-session: opencv-contrib-python-headless restored (numpy pinned back to 2.1.3 after a
  transient 2.5.5 install), `pip check` clean; HANDOFF.md continuation prompt scrubbed of hardcoded home paths
  (the repo hygiene test rejects them).
- Full-suite final state: 25 tracked notebooks, all executed with 0 cell errors; 188 tests passed; all hygiene
  and integrity checks passed; vault wikilinks 1095 checked, 0 broken.

## Session 7 — issues #20, #21, #23 (stage-4 vault sweep + Nagao geometry fix; post-consolidation topology)

**Context:** the session before this one (outside the issue loop) consolidated
both repositories per user directive: `APSD_TAI_LAB` now has a SINGLE `main`
branch (old `master` + `image-processing-data-science` deleted, both fully
contained in `main`), and the vault's `main` was emptied with all content
preserved on `image-processing-data-science` (which also adopted the
`TAI/` → `Image Processing/` folder rename). AGENT.md §1/§4 updated to match.

**Completed work** (vault commits `0b5ac54`, `b4362a4`, `7dd4ccf` on
`image-processing-data-science`; issues #20/#21/#23 closed with evidence
comments; user directive: "close more issues" — three closed):

1. **#20 — 05.1 complete Ch6 EDA summary:** cat-categorical analysis
   (`pd.cut` + `pd.crosstab` + heatmap, normalize reading rules), multivariate
   views (`pairplot`/`FacetGrid`/grouped bar), skew/kurtosis
   Recommended-Actions table (6 readings → actions), instructor's Pearson
   Cov/σ notation (identity proven by executed snippet: `x.cov(y)/(x.std()*y.std()) == x.corr(y)`),
   APDS/09 iris project cross-reference with section-by-section concept map.
2. **#21 — 04.1–04.6 complete Ch5 coverage:** 04.1 missingness audit
   (`values.any()`/%-table/`sns.heatmap(df.isnull())`) + `ffill`/`bfill` +
   executed SimpleImputer-vs-KNNImputer comparison; 04.2 4-panel outlier
   treatment figure + `scipy.stats.zscore` scatter + duplicates
   (`duplicated(subset=)`) + type validation (`to_numeric`/`to_datetime`/
   `astype("category")`/NaT/NaN) + p.20 `median_income=.mean()` quirk callout;
   04.3 `LabelEncoder` + regex cleaning + `unidecode` + p.22
   unidecode-after-regex quirk (both orders executed: `['Stif','Bjaa']` vs
   `['Setif','Bejaia']`); 04.4 MinMax/Robust/Normalizer(l1/l2) + L1-diamond
   vs L2-circle annotated scatter; 04.5/04.6 Lab Companion sections synced
   with the APDS/08 notebooks (all quoted numbers verified against them or
   recomputed).
3. **#23 — Nagao 3x3 centre clique everywhere + dedup:** 02.6 rewritten as
   THE canonical concept note (3x3 centre 9 px + 8 peripheral 7-px regions,
   |R_k| formulas, 5x5/7x7/9x9 sizing table [9,7×8]/[9,14×4,12×4]/
   [25,23×4,19×4], course-wording callout); 09.5 rewritten as the lab
   walkthrough with `build_nagao_masks`+`filtreNagao` embedded
   byte-identical to `TAI/utils/filters.py`; Libraries/26 geometry fixed +
   worked-example R0 row recomputed (n=9, 121.111, 1916.765) + timings
   re-measured (A 6.97/B 0.104/C 0.010/D 0.046 s) + §2.1/§3 de-duplicated
   into links; Libraries/20 Nagao section reduced to positioning + links
   (divergent inline implementation removed); 26.5/20.5/Quiz-TAI-02 wording
   fixes. Acceptance greps clean (0 five-px-cross matches vault-wide).

**Validation:** all python blocks of every touched note executed in reading
order (0 errors; 04.6's full titanic pipeline re-printed the companion's
exact accuracies 0.8212/0.8045); quiz validator 30/30 ALL VALID; wikilinks
164 notes / 1118 links / 0 broken (checked after each commit).

**New verified facts / lessons (Session 7)**
- Canonical `filtreNagao` uses `cv2.BORDER_REFLECT`; the vault's four
  reference implementations use `BORDER_REFLECT_101`: pixel-identical on the
  interior, rim-only difference (91.4% overall / 100% interior on 64x64
  random, gaps to 141 levels). Documented in 09.5 + Libraries/26 §7.
- The Libraries/26 §9 rng(0) tie example survives the 3x3-centre change
  VERBATIM (same pixel (50,56), same R3/R7 variances, same outputs 121/143);
  256x256 rates: A vs C 2/65536 px, A vs B 1, A vs D 0.
- Draft factual errors caught by the verify-before-commit loop this session:
  fare kurtosis is 33.4 (not 33.2); the within-setosa +0.74 is the
  sepal_length~sepal_width pair (pooled −0.12), NOT sepal_width~petal_length
  (that one is −0.43 pooled → +0.18 within); titanic women 74.2%/men 18.9%
  (not 75.3/20.5). Always recompute before quoting.
- seaborn `load_dataset('titanic')` works in this sandbox (network OK);
  `sns.load_dataset('iris')` was NOT used — the 05.1/09.5 snippets load iris
  via sklearn's local `load_iris()` (no network, mirrors APDS/09).
- A dict-built `None` is `NaN` for `isnull()`, but the string `"None"` from a
  CSV is invisible until text normalization (documented in 04.1).
- The `.5` sheets' "Motor-Recall Code Templates" blocks are fragmentary by
  design (placeholder variables like `py`/`px`) — they do not execute as
  whole blocks; their factual claims must be re-verified by script instead
  (26.5's were). Full `.5` code hygiene remains #33's scope.
- Session helpers live in the agent workspace scripts folder:
  `vault_exec.py` (execute every python block of a vault note in reading
  order, `display` shimmed), `close_issueN.py` pattern (REST comment+close;
  token in `repos/.token`), `verify_nagao_23*.py`, `issue2*_gen*.py`.


## Session 8 — issue #24 (Bilateral: one canonical treatment aligned with the real `filtrebilateral`)

**Context:** continuation session; both repos cloned fresh (lab `main`,
vault `image-processing-data-science`), PAT re-embedded in the vault push
URL (`git remote set-url`). `gh` still absent — REST via `urllib` helper
scripts under the workspace `scripts/` folder. Open issues at start: #2, #24,
#25–#29, #30–#33, #35.

**Completed work** (vault commit `c0ffcde`; issue #24 closed with evidence
comment):

1. **`Libraries/25` rebuilt as the single canonical Bilateral treatment**,
   aligned with the REAL `TAI/utils/filters.py:filtrebilateral` (per the
   Session-7 caution: no range LUT — per-shift vectorized
   shift-accumulation):
   - §6.1 embeds `_validate_odd` + `filtrebilateral` **byte-identical**
     (automated diff vs the module source: exact match) + pattern
     explanation (offsets-not-pixels loops, scalar `math.exp` spatial,
     vectorized `np.exp` range, reflect padding = `BORDER_REFLECT_101`,
     square window, `1e-12` guard) + measured timings (canonical 1.3 ms vs
     naive 17.0 ms on 48×48; 26 ms on 256×256).
   - §6.2 `bilateral_naive` repositioned as the pedagogical per-pixel
     translation (the `filtreMoyenne_naif_boucles` role); verified max-0
     difference vs the canonical form.
   - §6.3 range-LUT demoted to *optional optimization*, source-verified
     against OpenCV 4.x (`bilateral_filter.dispatch.cpp`:
     `color_weight[i] = (float)std::exp(i*i*gauss_color_coeff)`; consumed
     as `color_weight[std::abs(val - val0)]` in `bilateral_filter.simd.hpp`);
     verified LUT values 0.8825 / 0.3247 / 0.0111 (σ_r=40).
   - **New §7.1 — OpenCV's disk-shaped spatial window** (source-verified
     `if (r > radius) continue;`): d=7 disk keeps 29/49 offsets; square
     (canonical) vs cv2 = max 14 levels at d=7 (mean 1.74) and max 6 at d=9
     (mean 0.76, seed 24); **adopting the disk rule reproduces cv2
     bit-exactly** (max 0, mean 0.0000 at d=7/9/11, borders included).
     TP2 course preset `d=7, sigmaColor=40, sigmaSpace=40` added (instructor-
     prescribed, `tp2_enonce_fr.pdf` Ex. 2 d).
   - §9 rebuilt as a 3-row verified agreement table + TP2 lab reproduction
     on the seeded lab inputs (cameraman + var-100 seed-42): cv2 preset
     (7,40,40) vs `filtrebilateral(7, 2.0, 40.0)` → **PSNR 47.05 dB**
     ("similar behaviour" — deliberately cross-parameter); 30.03 vs 30.29 dB
     against the clean reference over the 28.13 dB noisy baseline.
2. **`Libraries/20` §3 reduced to positioning + canonical links** (mirrors
   the #23 Nagao pattern); duplicated formula block + symbol list removed.
3. **`Libraries/25.5`** — canonical signature row
   (`filtrebilateral(img, k, sigma_s, sigma_r)`); LUT relabeled optional in
   the syntax matrix, §3.3 and the checklist (removed the old "exam expects
   the table lookup form" contradiction); §4 Motor-Recall rewritten to the
   canonical per-shift template — line-for-line the module body
   (programmatically verified) — + TP2 preset one-liner.
4. **`Libraries/20.5`** — one canonical from-scratch signature row added.
5. **`Image Processing/02.7`** — deep-dive pointer updated only (canonical
   implementation, disk-window semantics); stays the compact concept note.

**Validation:** byte-identical embed check OK; all 6 python blocks of
`Libraries/25` execute in reading order **0 errors** (legacy §7 API demo and
§8 color demo made runnable in the process); `Libraries/20` block OK;
wikilinks **164 notes / 1122 links / 0 broken**; no lab-repo or quiz files
touched (lab suite unaffected).

**New verified facts / lessons (Session 8)**
- **`cv2.bilateralFilter` uses a DISK, not the square window** (source:
  `bilateral_filter.dispatch.cpp` skips offsets with `r > radius`; at d=7
  the disk keeps 29 of 49 offsets). Square-vs-disk deviates max 14 levels
  at d=7; a disk-rule manual implementation reproduces cv2 exactly. This
  supersedes the old §9 explanation ("LUT rounding and border handling").
- OpenCV 4.x 8U bilateral precomputes the 256-entry color-weight LUT
  (source-verified in `bilateral_filter.dispatch.cpp` / `.simd.hpp`).
- `np.pad(mode="reflect")` == `BORDER_REFLECT_101` confirmed bit-exactly on
  border pixels (full-image max 0 including borders at d=7/9/11).
- **Toolchain quirks for future sessions:** (a) the Bash tool's DISPLAY
  strips the two characters ESC + `[m` — text like `space_weight[maxk]`
  renders as `space_weightaxk]`; files on disk are unaffected — verify
  bytes with Python (`chr(91)`) when a `[m` sequence matters; (b) Write/Edit
  can mangle a `)` directly before a closing quote in rare code-heavy
  payloads — always re-read files after writing; (c) multi-pattern `rg`
  sweeps over the vault can hit the 2-minute timeout — use single-pass
  Python scanners instead.
- Reusable session helpers now live in the workspace `scripts/` folder (outside both repos):
  `vault_exec.py` (execute every python block of a note in reading order,
  `display` shimmed, Agg), `find_inbound.py` (single-pass inbound-link
  map), `issue24_verify.py` (numeric-claim re-measurement pattern),
  `issue24_byte_identical.py`, `issue24_template_check.py`,
  `close_issue24.py` (REST comment+close via `urllib` — avoids curl quoting
  issues).

## Remaining / blocked
- 11 issues open: #2 (awaiting TP1 handout text — placeholders committed),
  #25 (Contour Stencils 12-stencil fix — NEXT), #26–#29 (vault 09.x sync
  with TAI labs), #30–#32 (.5 exam-prep), #33 (.5 sweep + phantom refs),
  #35 (roadmap unification). Nothing else blocked.
- Tracker gap (carried from Session 6, still unopened): no issue covers
  syncing vault tutorials `03.2`–`03.5` with the updated APDS/05–07
  notebooks (column names, `>= 15` vs `> 15`). Fold into a future session or
  open a new issue.
- #25 cautions (verified in Session 1, do not re-litigate): the canonical
  SR is `TAI/utils/super_res.py` — full Getreuer 2009, **12 oriented
  stencils, output `(2h, 2w)`**; vault `09.8` / `Libraries/24` / `24.5`
  teach a 2-diagonal `(2H-1, 2W-1)` toy and even assert "never `(2H, 2W)`" —
  wrong for the lab. Correct to the 12-stencil form; a simplified hand
  example may survive ONLY as a clearly labelled pedagogical reduction.
  Sources: `TAI/utils/super_res.py`, `TAI/docs/references/
  getreuer_2009_contour_stencils.pdf`, `tp2_enonce_fr.pdf` Ex 6, and the
  `TAI/04_TP2_Super_Resolution` notebook.

## Session 9 — COMPLETE (issues #25, #26, #27, #28, #29)

**Goal:** execute the five vault 09.x/24.x sync issues left by Session 8
(#25 Contour Stencils, #26 TP1 labs, #27 TP2 filtering, #28 morphology,
#29 contrast), one commit + issue-close each, per the user's request to
solve 5+ issues this session.

### Completed work (vault branch `image-processing-data-science`)
1. **#25 — Contour Stencils** (commit `4f4c2d7`): `Libraries/24` rewritten
   around the canonical 12-stencil Getreuer pipeline (weighted/
   length-normalized TV, G_rho smoothing, YCrCb l1 norm, 4 rule groups,
   `(2h, 2w)` assembly with shared mid-point averaging + rim extrapolation,
   pyramid 4x; embedded compressed reproduction verified BIT-EXACT vs
   `TAI/utils/super_res.py` at rho=0). `Libraries/24.5` wrong claims
   inverted ((2H-1,2W-1)->(2h,2w); 6 unsolved drills + executed key).
   `Image Processing/09.8` rewritten as the TAI/04 lab walkthrough with
   measured benchmarks (bicubic 31.96 dB / stencils 27.52 dB at 2x on the
   demo set; grid-alignment caveat documented). **Quiz 09 + Quiz L04
   corrected** (511x511 wrong answer -> 512x512; stage matching rebuilt on
   the canonical pipeline; L04 match item q) -> (2H,2W) lattice).
2. **#26 — 09.1/09.2 sync** (commit `49a1f96`): 09.1 = TAI/00 + TP1 Exo 1-3
   (toolchain table, unified layout, the `a[2:3][1:3]`->(0,5) vs
   `a[2:3,1:3]`->(1,2) trap, seuillage_fixe_perso parity 120,822 fg px);
   09.2 = TAI/01 notebooks 01/03/04 (corrected verification discipline for
   the six derived images, calcul_histogramme_perso bit-for-bit x4,
   per-workload timing semantics). Quiz 09 manual_threshold ->
   seuillage_fixe_perso.
3. **#27 — 09.3/09.4 sync** (commit `6bba9dc`): 09.3 = noise laws (the
   corrected 18.59 dB theoretical at var=900, measured 19.10 + clipping
   explanation), filter parity, PSNR benchmark table (median +10.35 dB on
   S&P, bilateral only baseline-beater on Gaussian); 09.4 = graded (a)/(b)
   (complexity ladder, corrected 4-distinct-corners SAT formula, canonical
   filtreMoyenne_integrale/separable embedded + sanity-checked identical,
   ~140-180x speedups, slide-42 adaptive + impulse fallback + Lee MMSE,
   full comparison table). Quiz 09 fast_box_filter_integral ->
   filtreMoyenne_integrale.
4. **#28 — 09.6 sync** (commit `21112c6`): polarity-aware Otsu (threshold
   162, border median 153), 3x3/5x5/7x7 grid with all-12 parity Exact
   (neutral padding + kernel reflection documented), counting ladder
   75->22->20->19 (closing+hole-fill+opening, iterative erosion,
   distance-peaks+watershed), Zhang-Suen conditions + cv2.ximgproc vs
   custom (25 ms vs 61 ms, NOT bit-identical ~1687 px, border/tie order -
   reported honestly), opencv-contrib requirement stated.
5. **#29 — 09.7 sync** (commit `7c23d8d`): measured input ranges, canonical
   4-parameter expansionHisto embedded, the verified colour nuance
   (grayscale bit-for-bit 0; colour 48 levels because cv2.normalize uses
   GLOBAL cross-channel min/max vs per-channel - manual global stretch
   reproduces cv2 exactly), global/AHE/CLAHE verification (exact / 46.32 dB
   / 53.79 dB), Lab-L colour preservation, L-std ladder 30.3->71.2->52.4
   ->34.2 with the clinical CLAHE rationale.

**Validation per issue:** `vault_exec.py` on every touched note (0 failures;
every cited number reproduces live), `quiz_validator.py` ALL VALID on every
touched quiz, `check_wikilinks.py` 164-165 notes / ~1133 links / 0 broken,
lab suite re-run at the end (see below). All 5 issues closed with evidence
comments via REST.

**Lab-repo fix (this session):** Session 8's HANDOFF commit introduced 7
absolute home-directory sandbox paths, breaking
`tests/test_repo_hygiene.py::test_no_hardcoded_home_paths`. Scrubbed them
to workspace-relative wording (see this commit); the suite is green again.

### Verified findings / lessons (Session 9)
- `cv2.normalize(NORM_MINMAX)` on colour uses the GLOBAL cross-channel
  min/max; the assignment's per-channel expansionHisto diverges by up to 48
  levels on the fundus image (verified: manual global stretch ==
  cv2.normalize bit-for-bit).
- `cv2.ximgproc.thinning(THINNING_ZHANGSUEN)` and the pure-NumPy
  `custom_zhang_suen_thinning` are NOT bit-identical (~1687/8740 skeleton
  px differ on imb1) — border handling and simultaneous-deletion tie
  ordering; the notebook reports this honestly and so do the notes.
- The TAI notebooks' markdown "Expected PSNR" table already carries the
  corrected 18.59 dB value (var=900); measured is 19.10 dB due to [0,255]
  clipping reducing effective MSE (documented in 09.3).
- Quiz validator gotcha: answer text must EXACTLY repeat the option text;
  no standalone explanation paragraphs between callout blocks; the lone `>`
  separator between example groups must have no blank line before it.
- vault_exec semantics that work: shared namespace across a note's python
  blocks in reading order + chdir into the lab repo (bootstrap needs cwd
  inside the repo); bare fences (no language) are non-executable displays —
  use them for intentionally-buggy drill code.
- Embedded def blocks with `-> np.ndarray` annotations need `numpy as np`
  in scope BEFORE the def (annotations evaluate at def time).

## Remaining / blocked
- 7 issues open: #2 (awaiting TP1 handout text — placeholders committed),
  #30 (Core Python 00.5 construction guide), #31 (01.5/02.5/03.5 upgrade),
  #32 (10.5/23.5 upgrade), #33 (.5 sweep + phantom refs), #35 (roadmap
  unification), **#36 NEW** (legacy `Images/...` demo paths in
  `Libraries/15`, `16`, `18`, `21` — verified this session; fold the
  vault-tutorials 03.2-03.5 sync gap into it or a sibling).
- Nothing else blocked. Issues #25-#29 all closed with evidence comments.

## Next session
**Work issue #30** (create the Core Python Handwritten Construction guide
`Libraries/00.5...`), then #31, #32 in order; #33 after them; #35 last.
Open issues now: #2, #30, #31, #32, #33, #35, #36.

**Continuation prompt (paste as the first message):**
> Repositories: the lab clone (folder `APSD_TAI_LAB`, branch `main` — the
> only branch) and the vault clone (folder `UMBB-Master-1`, branch
> `image-processing-data-science`; its `main` stays empty; the vault's
> `TAI/` folder is now `Image Processing/`). Re-embed the PAT into the
> vault push URL if a fresh clone (`git remote set-url origin
> https://<PAT>@github.com/Vtheonly/UMBB-Master-1.git`). Python: system
> interpreter (opencv-contrib-python-headless installed for cv2.ximgproc).
> Read `AGENT.md` and `HANDOFF.md` first, then `GET /repos/Vtheonly/
> APSD_TAI_LAB/issues?state=open` (REST; token from the lab push URL; the
> workspace `close_issue.py` helper shows the urllib comment+close
> pattern). Work the GitHub issues in order: #30 first (Core Python 00.5
> handwritten construction guide under `Libraries/`, per AGENT.md section 5
> standards: problem-to-code method, clean multiline Python, unsolved paper
> drills with executed answer keys), then #31 (01.5/02.5/03.5 upgrade) and
> #32 (10.5/23.5). For each one: verify against the sources (course PDFs,
> `TAI/utils/*.py`, lab notebooks), edit through a persisted script in the
> workspace `scripts/` folder, execute every python block you add or touch
> (`python scripts/vault_exec.py <note.md>` from the workspace), validate
> (`python scripts/check_wikilinks.py <vault-clone>`, quiz validator for
> quiz edits, lab suite only if lab files change), commit and push (vault
> -> `image-processing-data-science`, lab -> `main`), close the issue with
> an evidence comment, then update `HANDOFF.md`. Beware: Bash output
> display strips the sequence ESC+backtick; verify such bytes with Python;
> never write `/home/<user>/` absolute paths into committed files (repo
> hygiene test forbids them).
