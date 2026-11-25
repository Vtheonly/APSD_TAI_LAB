"""TP2 super-resolution: bilinear 2x and Contour-Stencil interpolation.

Functions
---------
super_resolution_bilineaire_2x        from-scratch bilinear 2x upsampling
                                      with OpenCV pixel-centre alignment.
super_resolution_contour_stencils_2x  adaptive Getreuer (2009) contour-stencil
                                      interpolation (12 oriented stencils).
discover_sr_triplets                  dataset discovery: official
                                      ``Images_TP2_EXO6_SR`` archive when
                                      present, otherwise a deterministic
                                      5-image demonstration set.

Contour stencils (Getreuer, SPIE 2009)
--------------------------------------
Each LR cell is classified against 12 oriented stencils by their total
variation (TV); the stencil with the smallest TV best explains the local
edge orientation. Interpolation rules then place the four mid-points and the
cell centre according to the winning orientation, and shared mid-points are
averaged between adjacent cells — producing sharp, ringing-free edges.
Colour images measure TV in YCrCb with the l1 vector norm (Remark 3 of the
paper); the TV maps are smoothed by a Gaussian G_rho (Remark 1).
"""

from __future__ import annotations

import math
from pathlib import Path

import cv2
import numpy as np


# ---------------------------------------------------------------------------
# Dataset discovery
# ---------------------------------------------------------------------------
def discover_sr_triplets(images_dir: Path, outputs_dir: Path):
    """Locate (or synthesise) super-resolution LR/HR triplets.

    Resolution order:
      1. official ``Images_TP2_EXO6_SR`` archive (23 triplets) consolidated
         under ``images_dir`` or sitting next to the repository root;
      2. deterministic 5-image demonstration set generated inside
         ``outputs_dir`` from standard TAI images.

    Returns ``(label, triplets)`` where each triplet is
    ``(hr_path, lr256_path, lr128_path)`` sorted numerically 1..N so the
    HR/LR256/LR128 files can never misalign.
    """
    images_dir = Path(images_dir)
    outputs_dir = Path(outputs_dir)

    # Case A: official dataset already consolidated into TAI/images/
    hr_files = sorted(
        images_dir.glob("tp2_exo6_sr_hr_gt_512x512_*"),
        key=_numeric_suffix,
    )
    lr256_files = sorted(
        images_dir.glob("tp2_exo6_sr_lr_256x256_*"),
        key=_numeric_suffix,
    )
    lr128_files = sorted(
        images_dir.glob("tp2_exo6_sr_lr_128x128_*"),
        key=_numeric_suffix,
    )
    if hr_files and len(hr_files) == len(lr256_files) == len(lr128_files):
        return "Consolidated dataset in TAI/images", list(zip(hr_files, lr256_files, lr128_files))

    # Case B: extracted Images_TP2_EXO6_SR archive folder
    for base in (
        images_dir / "Images_TP2_EXO6_SR",
        images_dir.parent / "Images_TP2_EXO6_SR",
        images_dir.parent / "Images" / "Images_TP2_EXO6_SR",
    ):
        hr_dir, lr2_dir, lr4_dir = base / "HR_GT_512x512", base / "LR_256x256", base / "LR_128x128"
        if hr_dir.is_dir() and lr2_dir.is_dir() and lr4_dir.is_dir():
            triplets = []
            for i in range(1, 24):
                hr_match = list(hr_dir.glob(f"HR_GT_{i}.*"))
                l2_match = list(lr2_dir.glob(f"LR_256_{i}.*"))
                l4_match = list(lr4_dir.glob(f"LR_128_{i}.*"))
                if hr_match and l2_match and l4_match:
                    triplets.append((hr_match[0], l2_match[0], l4_match[0]))
            if triplets:
                return f"Official dataset ({base})", triplets

    # Case C: deterministic local demonstration set
    demo_dir = outputs_dir / "exo6_demo_dataset"
    for sub in ("HR_GT_512x512", "LR_256x256", "LR_128x128"):
        (demo_dir / sub).mkdir(parents=True, exist_ok=True)
    seed_imgs = [
        "tp1_tp2_compteur_water_meter.jpg",
        "tp1_tp2_cameraman_gray.bmp",
        "tp1_exo4_exo5_peppers_color.bmp",
        "tp1_tp2_sample_barbara_portrait.bmp",
        "tp1_tp2_sample_houses_street.bmp",
    ]
    triplets = []
    for idx, fname in enumerate(seed_imgs, start=1):
        src = cv2.imread(str(images_dir / fname), cv2.IMREAD_COLOR)
        if src is None:
            continue
        hr = cv2.resize(src, (512, 512), interpolation=cv2.INTER_CUBIC)
        l2 = cv2.resize(hr, (256, 256), interpolation=cv2.INTER_AREA)
        l4 = cv2.resize(hr, (128, 128), interpolation=cv2.INTER_AREA)
        p_hr = demo_dir / "HR_GT_512x512" / f"HR_GT_{idx}.png"
        p_l2 = demo_dir / "LR_256x256" / f"LR_256_{idx}.png"
        p_l4 = demo_dir / "LR_128x128" / f"LR_128_{idx}.png"
        cv2.imwrite(str(p_hr), hr)
        cv2.imwrite(str(p_l2), l2)
        cv2.imwrite(str(p_l4), l4)
        triplets.append((p_hr, p_l2, p_l4))
    return "Deterministic demonstration set (Images_TP2_EXO6_SR not found)", triplets


def _numeric_suffix(path: Path) -> list:
    """Sort key extracting trailing digits so 2 comes before 10."""
    stem = Path(path).stem
    digits = "".join(ch for ch in stem.split("_")[-1] if ch.isdigit())
    return [int(digits) if digits else 0, str(path)]


# ---------------------------------------------------------------------------
# Bilinear 2x
# ---------------------------------------------------------------------------
def super_resolution_bilineaire_2x(image, opencv_align: bool = True) -> np.ndarray:
    """From-scratch bilinear interpolation by an exact factor of 2.

    With ``opencv_align=True`` the sampling grid matches OpenCV's
    pixel-centre convention — the source coordinate of output row ``i`` is
    ``(i + 0.5)/2 - 0.5`` — so the result matches
    ``cv2.resize(..., interpolation=cv2.INTER_LINEAR)`` up to rounding.
    """
    img = image.astype(np.float64)
    h, w = img.shape[:2]
    out_h, out_w = 2 * h, 2 * w

    if opencv_align:
        ys = np.clip((np.arange(out_h, dtype=np.float64) + 0.5) / 2.0 - 0.5, 0.0, h - 1.0)
        xs = np.clip((np.arange(out_w, dtype=np.float64) + 0.5) / 2.0 - 0.5, 0.0, w - 1.0)
    else:
        ys = np.clip(np.arange(out_h, dtype=np.float64) / 2.0, 0.0, h - 1.0)
        xs = np.clip(np.arange(out_w, dtype=np.float64) / 2.0, 0.0, w - 1.0)

    y0 = np.floor(ys).astype(np.int64)
    x0 = np.floor(xs).astype(np.int64)
    y1 = np.minimum(y0 + 1, h - 1)
    x1 = np.minimum(x0 + 1, w - 1)
    wy = (ys - y0)[:, None]
    wx = (xs - x0)[None, :]

    if img.ndim == 3:
        wy = wy[:, :, None]
        wx = wx[:, :, None]

    v00 = img[y0[:, None], x0[None, :]]
    v01 = img[y0[:, None], x1[None, :]]
    v10 = img[y1[:, None], x0[None, :]]
    v11 = img[y1[:, None], x1[None, :]]

    out = (
        (1.0 - wy) * (1.0 - wx) * v00
        + (1.0 - wy) * wx * v01
        + wy * (1.0 - wx) * v10
        + wy * wx * v11
    )
    return np.clip(np.round(out), 0, 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# Contour-stencil interpolation (Getreuer 2009)
# ---------------------------------------------------------------------------
def super_resolution_contour_stencils_2x(image, rho: float = 0.5) -> np.ndarray:
    """Adaptive 2x interpolation by contour stencils (Getreuer, SPIE 2009).

    Pipeline
    --------
    1. Directional differences (horizontal, vertical, both diagonals) are
       computed on the edge-padded image; colour images use the l1 norm of
       the YCrCb difference vector.
    2. For each of the 12 oriented stencils the weighted total variation
       ``TV(S)`` is accumulated per LR cell and smoothed by a Gaussian
       ``G_rho``.
    3. ``argmin`` over the 12 TV maps selects the local stencil orientation.
    4. Four interpolation rule groups place the N/S/W/E mid-points and the
       cell centre X; mid-points shared between adjacent cells are averaged.

    The output has exactly ``(2h, 2w)`` pixels with values in [0, 255].
    """
    h, w = image.shape[:2]
    if image.ndim == 3:
        feat = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb).astype(np.float64)
        img_f = image.astype(np.float64)
        pad_feat = np.pad(feat, ((1, 1), (1, 1), (0, 0)), mode="edge")
        diff_norm = lambda a, b: np.sum(np.abs(a - b), axis=2)
    else:
        img_f = image.astype(np.float64)
        pad_feat = np.pad(img_f, ((1, 1), (1, 1)), mode="edge")
        diff_norm = lambda a, b: np.abs(a - b)

    # Directional differences on the padded grid (H+2, W+2)
    dh = diff_norm(pad_feat[:, :-1], pad_feat[:, 1:])     # (H+2, W+1)
    dv = diff_norm(pad_feat[:-1, :], pad_feat[1:, :])     # (H+1, W+2)
    da = diff_norm(pad_feat[:-1, :-1], pad_feat[1:, 1:])  # main diagonal '\'
    db = diff_norm(pad_feat[1:, :-1], pad_feat[:-1, 1:])  # anti-diagonal '/'

    ch, cw = h - 1, w - 1  # number of LR cells
    sl = lambda arr, r0, c0: arr[r0:r0 + ch, c0:c0 + cw]
    s2 = math.sqrt(2.0)

    # 12 stencils (edges in the local 4x4 neighbourhood), each entry:
    # (list of (diff_key, row, col, weight), normalising length |S|)
    stencil_defs = [
        # 0: vertical |
        ([("dv", 0, 1, 22), ("dv", 1, 1, 43), ("dv", 2, 1, 22),
          ("dv", 0, 2, 22), ("dv", 1, 2, 43), ("dv", 2, 2, 22)], 174.0),
        # 1: horizontal -
        ([("dh", 1, 0, 22), ("dh", 1, 1, 43), ("dh", 1, 2, 22),
          ("dh", 2, 0, 22), ("dh", 2, 1, 43), ("dh", 2, 2, 22)], 174.0),
        # 2: anti-diagonal / (45 deg)
        ([("db", 1, 0, 16), ("db", 0, 1, 16), ("db", 1, 1, 59),
          ("db", 2, 1, 16), ("db", 1, 2, 16)], 123.0 * s2),
        # 3: main diagonal \ (-45 deg)
        ([("da", 1, 2, 16), ("da", 0, 1, 16), ("da", 1, 1, 59),
          ("da", 2, 1, 16), ("da", 1, 0, 16)], 123.0 * s2),
        # 4: gentle / (~26.6 deg)
        ([("db", 0, 0, 17), ("dh", 0, 1, 22), ("dh", 2, 0, 17),
          ("db", 1, 1, 34), ("dh", 1, 2, 17), ("dh", 3, 1, 22), ("db", 2, 2, 17)],
         78.0 + 68.0 * s2),
        # 5: steep \ (~63.4 deg)
        ([("da", 0, 2, 17), ("dv", 1, 3, 22), ("dv", 0, 1, 17),
          ("da", 1, 1, 34), ("dv", 2, 2, 17), ("dv", 1, 0, 22), ("da", 2, 0, 17)],
         78.0 + 68.0 * s2),
        # 6: gentle \ (~-26.6 deg)
        ([("dh", 0, 1, 22), ("da", 0, 2, 17), ("dh", 1, 0, 17),
          ("da", 1, 1, 34), ("dh", 2, 2, 17), ("da", 2, 0, 17), ("dh", 3, 1, 22)],
         78.0 + 68.0 * s2),
        # 7: steep / (~63.4 deg)
        ([("db", 0, 0, 17), ("dv", 1, 0, 22), ("dv", 0, 2, 17),
          ("db", 1, 1, 34), ("dv", 2, 1, 17), ("dv", 1, 3, 22), ("db", 2, 2, 17)],
         78.0 + 68.0 * s2),
        # 8: mixed /-H-/
        ([("db", 1, 0, 34), ("dh", 1, 1, 39), ("dh", 2, 1, 39), ("db", 1, 2, 34)],
         78.0 + 68.0 * s2),
        # 9: mixed \-H-\
        ([("da", 1, 0, 34), ("dh", 1, 1, 39), ("dh", 2, 1, 39), ("da", 1, 2, 34)],
         78.0 + 68.0 * s2),
        # 10: mixed \-V-\
        ([("da", 0, 1, 34), ("dv", 1, 1, 39), ("dv", 1, 2, 39), ("da", 2, 1, 34)],
         78.0 + 68.0 * s2),
        # 11: mixed /-V-/
        ([("db", 0, 1, 34), ("dv", 1, 1, 39), ("dv", 1, 2, 39), ("db", 2, 1, 34)],
         78.0 + 68.0 * s2),
    ]

    diff_lookup = {"dh": dh, "dv": dv, "da": da, "db": db}
    tv_maps = np.empty((12, ch, cw), dtype=np.float64)
    for idx, (edges, norm_len) in enumerate(stencil_defs):
        acc = np.zeros((ch, cw), dtype=np.float64)
        for dkey, r0, c0, weight in edges:
            acc += weight * sl(diff_lookup[dkey], r0, c0)
        tv_map = acc / norm_len
        if rho > 0.0:
            tv_map = cv2.GaussianBlur(tv_map, (3, 3), sigmaX=rho, borderType=cv2.BORDER_REFLECT)
        tv_maps[idx] = tv_map

    best = np.argmin(tv_maps, axis=0)  # (ch, cw)

    # Cell corner values
    tl = img_f[:-1, :-1]
    tr = img_f[:-1, 1:]
    bl = img_f[1:, :-1]
    br = img_f[1:, 1:]

    mid_n_bil = 0.5 * (tl + tr)
    mid_s_bil = 0.5 * (bl + br)
    mid_w_bil = 0.5 * (tl + bl)
    mid_e_bil = 0.5 * (tr + br)
    avg4 = 0.25 * (tl + tr + bl + br)
    diag_anti = 0.5 * (bl + tr)
    diag_main = 0.5 * (tl + br)

    n_val = mid_n_bil.copy()
    s_val = mid_s_bil.copy()
    w_val = mid_w_bil.copy()
    e_val = mid_e_bil.copy()
    x_val = avg4.copy()

    # Group B: pure diagonals (2) '/' and (3) '\'
    m2 = (best == 2)
    x_val[m2] = diag_anti[m2]
    m3 = (best == 3)
    x_val[m3] = diag_main[m3]

    # Group C: steep orientations (4, 5, 6, 7)
    m4 = (best == 4)
    w_val[m4] = e_val[m4] = x_val[m4] = diag_anti[m4]
    m5 = (best == 5)
    n_val[m5] = s_val[m5] = x_val[m5] = diag_main[m5]
    m6 = (best == 6)
    w_val[m6] = e_val[m6] = x_val[m6] = diag_main[m6]
    m7 = (best == 7)
    n_val[m7] = s_val[m7] = x_val[m7] = diag_anti[m7]

    # Group D: mixed orientations (8, 9, 10, 11)
    m8 = (best == 8)
    w_val[m8] = mid_n_bil[m8]
    e_val[m8] = mid_s_bil[m8]
    m9 = (best == 9)
    e_val[m9] = mid_n_bil[m9]
    w_val[m9] = mid_s_bil[m9]
    m10 = (best == 10)
    n_val[m10] = mid_e_bil[m10]
    s_val[m10] = mid_w_bil[m10]
    m11 = (best == 11)
    n_val[m11] = mid_w_bil[m11]
    s_val[m11] = mid_e_bil[m11]

    # Assembly on the (2h, 2w) grid, averaging shared mid-points
    out_shape = (2 * h, 2 * w) + (() if image.ndim == 2 else (image.shape[2],))
    out = np.zeros(out_shape, dtype=np.float64)

    out[0:2 * h:2, 0:2 * w:2] = img_f                      # original pixels
    out[1:2 * h - 1:2, 1:2 * w - 1:2] = x_val             # cell centres

    # Horizontal mid-points (even row, odd col)
    out[0, 1:2 * w - 1:2] = n_val[0]
    out[2 * h - 2, 1:2 * w - 1:2] = s_val[-1]
    if h > 2:
        out[2:2 * h - 2:2, 1:2 * w - 1:2] = 0.5 * (s_val[:-1] + n_val[1:])

    # Vertical mid-points (odd row, even col)
    out[1:2 * h - 1:2, 0] = w_val[:, 0]
    out[1:2 * h - 1:2, 2 * w - 2] = e_val[:, -1]
    if w > 2:
        out[1:2 * h - 1:2, 2:2 * w - 2:2] = 0.5 * (e_val[:, :-1] + w_val[:, 1:])

    # Clean edge extrapolation for the last row/column
    out[:, -1] = out[:, -2]
    out[-1, :] = out[-2, :]

    return np.clip(np.round(out), 0, 255).astype(np.uint8)
