#!/usr/bin/env python3
"""NumPy slicing foundations: chained indexing vs. multi-axis tuple indexing.

This script documents (and corrects) a classic NumPy gotcha found in the
original course notes:

    array_now[2:3][1:3].shape   # comment claimed "(1, 5) why not (1, 3)"

The truth: the result is **(0, 5)** — not (1, 5) and not (1, 3)!

Why?
----
`array_now[2:3]` first extracts a *view* of shape (1, 5) (one row, five
columns). The second `[1:3]` then slices **axis 0 again** (rows!) of that
1-row view — rows 1 and 2 of a 1-row array simply do not exist, so the
result has shape (0, 5): *zero* rows, five columns.

Chained indexing is **not** row-then-column selection; each bracket applies
to the *first* axis of whatever the previous bracket returned. To select a
sub-block, pass a single **tuple** that indexes both axes at once:

    array_now[2:3, 1:3]    # shape (1, 2): one row, columns 1..2

Run this file directly (``python numpy_slicing_foundations.py``) — it is
also executed as a smoke check by the repository test-suite.
"""

import numpy as np


def build_demo_array() -> np.ndarray:
    """Return the 4x5 demo matrix used throughout the explanations."""
    return np.array(
        [
            [10, 20, 30, 40, 50],
            [60, 70, 80, 90, 100],
            [110, 120, 130, 140, 150],
            [160, 170, 180, 190, 200],
        ],
        dtype=np.uint64,
    )


def main() -> None:
    array_now = build_demo_array()
    print("Demo array (4 rows x 5 columns):")
    print(array_now)
    print()

    # ------------------------------------------------------------------
    # 1) The gotcha: chained indexing slices axis 0 TWICE
    # ------------------------------------------------------------------
    row_view = array_now[2:3]  # shape (1, 5): a view containing row 2
    print(f"array_now[2:3]      -> shape {row_view.shape}  (a 1-row *view*)")

    chained = array_now[2:3][1:3]
    print(
        f"array_now[2:3][1:3] -> shape {chained.shape}  "
        "<-- second bracket re-slices ROWS of the 1-row view: empty!"
    )
    assert chained.shape == (0, 5), "chained slicing must give (0, 5)"
    assert chained.size == 0

    # ------------------------------------------------------------------
    # 2) The fix: one tuple, both axes
    # ------------------------------------------------------------------
    block = array_now[2:3, 1:3]
    print(f"array_now[2:3, 1:3] -> shape {block.shape}  values:\n{block}")
    assert block.shape == (1, 2)
    assert block.tolist() == [[120, 130]]

    sub_block = array_now[2:4, 0:3]
    print(f"\narray_now[2:4, 0:3] -> shape {sub_block.shape}  values:\n{sub_block}")
    assert sub_block.shape == (2, 3)
    assert sub_block.tolist() == [[110, 120, 130], [160, 170, 180]]

    # ------------------------------------------------------------------
    # 3) Same rules for integer + slice mixes (still one tuple)
    # ------------------------------------------------------------------
    print(f"\narray_now[1, 0:3]  -> shape {array_now[1, 0:3].shape}  {array_now[1, 0:3]}")
    print(f"array_now[0:3, 2]  -> shape {array_now[0:3, 2].shape}  {array_now[0:3, 2]}")

    # ------------------------------------------------------------------
    # 4) Fancy (advanced) indexing copies instead of viewing
    # ------------------------------------------------------------------
    fancy = array_now[[1, 3]][:, [0, 2]]
    basic = array_now[1:4:2, 0:3:2]
    print(f"\narray_now[[1, 3]][:, [0, 2]] (fancy) -> shape {fancy.shape}:\n{fancy}")
    print(f"array_now[1:4:2, 0:3:2]  (slices) -> shape {basic.shape}:\n{basic}")

    print("\nAll assertions passed: tuple indexing selects sub-blocks, "
          "chained brackets re-slice axis 0.")


if __name__ == "__main__":
    main()
