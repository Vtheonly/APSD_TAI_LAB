# 04 — One-Million Record Streaming

Memory autopsy of large CSV loading: list-of-dicts vs. generator streaming.

## Contents
- `generate_dataset.py` — `generate_large_csv` (deterministic; skips regeneration if the file exists).
- `streaming_solutions.py` — `read_all_inefficient`, `stream_records`.
- `memory_benchmark.py` — benchmark harness (paths resolve from the script location; runs from any CWD).
- `streaming_analysis.ipynb` — interactive tracemalloc comparison.
- `large_patients.csv` — **generated at runtime and git-ignored** (deterministically regenerable, byte-identical every time).
