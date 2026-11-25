"""TP2 histogram contrast enhancement — from scratch, verified against OpenCV.

Functions
---------
expansionHisto            dynamic-range expansion (linear stretch).
egalisationHistoGlobale   global histogram equalisation (matches
                          ``cv2.equalizeHist`` on grayscale channels).
egalisationAHE            Adaptive Histogram Equalisation with bilinear
                          interpolation between tile mappings.
egalisationCLAHE          Contrast-Limited AHE with clip-limit
                          redistribution (mirrors ``cv2.createCLAHE``).
apply_on_gray_or_lab      applies any 2-D operator either directly (gray)
                          or on the L channel of Lab space (colour).

Colour images are enhanced on the L (lightness) channel of the Lab space so
that chrominance — and therefore the perceived colour balance — is preserved.
"""

from __future__ import annotations

import cv2
import numpy as np


# ---------------------------------------------------------------------------
# Dynamic-range expansion
# ---------------------------------------------------------------------------
def expansion_canal(canal, seuil: int = 0, Ymin: int = 0, Ymax: int = 255) -> np.ndarray:
    """Linear stretch of one channel from its effective range to [Ymin, Ymax].

    ``seuil`` ignores histogram bins with fewer than ``seuil + 1`` pixels
    when determining the effective min/max (robustness to outliers).
    """
    hist = np.bincount(canal.ravel(), minlength=256)
    valid = np.where(hist > seuil)[0]
    if len(valid) == 0:
        Xmin, Xmax = int(canal.min()), int(canal.max())
    else:
        Xmin, Xmax = int(valid[0]), int(valid[-1])
    if Xmax == Xmin:
        return np.full_like(canal, Ymin, dtype=np.uint8)
    alpha = (Ymin * Xmax - Ymax * Xmin) / (Xmax - Xmin)
    beta = (Ymax - Ymin) / (Xmax - Xmin)
    res = alpha + beta * canal.astype(np.float64)
    return np.clip(np.round(res), Ymin, Ymax).astype(np.uint8)


def expansionHisto(image, seuil: int = 0, Ymin: int = 0, Ymax: int = 255) -> np.ndarray:
    """Dynamic-range expansion, per channel for colour images.

    Y = Ymin + (X - Xmin) * (Ymax - Ymin) / (Xmax - Xmin)

    With ``seuil=0, Ymin=0, Ymax=255`` this matches
    ``cv2.normalize(img, 0, 255, NORM_MINMAX)`` bit-for-bit.
    """
    if image.ndim == 2:
        return expansion_canal(image, seuil, Ymin, Ymax)
    out = np.empty_like(image)
    for c in range(image.shape[2]):
        out[:, :, c] = expansion_canal(image[:, :, c], seuil, Ymin, Ymax)
    return out


# ---------------------------------------------------------------------------
# Histogram equalisation
# ---------------------------------------------------------------------------
def egalisation_globale_canal(canal) -> np.ndarray:
    """Global histogram equalisation of one channel.

    LUT(k) = round(255 * (CDF(k) - CDF_min) / (N - CDF_min))

    where CDF_min is the first non-zero cumulative count — the exact formula
    implemented by ``cv2.equalizeHist``.
    """
    hist = np.bincount(canal.ravel(), minlength=256)
    hc = np.cumsum(hist)
    nz = np.where(hc > 0)[0]
    if len(nz) == 0:
        return canal.copy()
    hc_min = hc[nz[0]]
    n_pix = canal.size
    if n_pix == hc_min:
        return canal.copy()
    lut = np.round(255.0 * (hc - hc_min) / (n_pix - hc_min))
    lut = np.clip(lut, 0, 255).astype(np.uint8)
    return lut[canal]


def egalisation_locale_blocs(canal, tile_grid=(8, 8), clip_limit=None) -> np.ndarray:
    """Tile-based local equalisation with bilinear stitching (AHE / CLAHE).

    1. The image is split into ``tile_grid`` tiles (reflect-padded).
    2. Each tile gets its own equalisation LUT.
    3. ``clip_limit`` (CLAHE): bins above the limit are clipped and the
       excess is redistributed uniformly.
    4. Output pixels are bilinearly interpolated between the 4 surrounding
       tile LUTs, eliminating visible tile seams.
    """
    h, w = canal.shape
    ty, tx = tile_grid
    pad_h = (ty - (h % ty)) % ty
    pad_w = (tx - (w % tx)) % tx
    padded = np.pad(canal, ((0, pad_h), (0, pad_w)), mode="reflect")
    ph, pw = padded.shape
    th, tw = ph // ty, pw // tx

    luts = np.zeros((ty, tx, 256), dtype=np.float64)
    n_tile = th * tw
    for iy in range(ty):
        for ix in range(tx):
            tile = padded[iy * th:(iy + 1) * th, ix * tw:(ix + 1) * tw]
            hist = np.bincount(tile.ravel(), minlength=256).astype(np.int64)
            if clip_limit is not None and clip_limit > 0:
                limit = max(1, int(round(clip_limit * n_tile / 256.0)))
                excess = np.sum(np.maximum(0, hist - limit))
                hist = np.minimum(hist, limit)
                avg_inc = excess // 256
                rem = int(excess % 256)
                hist += avg_inc
                if rem > 0:
                    step = max(1, 256 // rem)
                    indices = np.arange(0, 256, step)[:rem]
                    hist[indices] += 1
            hc = np.cumsum(hist).astype(np.float64)
            lut = np.round(255.0 * hc / max(1.0, hc[-1]))
            luts[iy, ix] = np.clip(lut, 0, 255)

    # Bilinear interpolation between tile-centre LUTs
    ys = np.arange(h, dtype=np.float64)
    xs = np.arange(w, dtype=np.float64)
    gy = (ys + 0.5) / th - 0.5
    gx = (xs + 0.5) / tw - 0.5
    y0 = np.clip(np.floor(gy).astype(np.int64), 0, ty - 1)
    x0 = np.clip(np.floor(gx).astype(np.int64), 0, tx - 1)
    y1 = np.clip(y0 + 1, 0, ty - 1)
    x1 = np.clip(x0 + 1, 0, tx - 1)
    wy = np.clip(gy - y0, 0.0, 1.0)[:, None]
    wx = np.clip(gx - x0, 0.0, 1.0)[None, :]

    v00 = luts[y0[:, None], x0[None, :], canal]
    v01 = luts[y0[:, None], x1[None, :], canal]
    v10 = luts[y1[:, None], x0[None, :], canal]
    v11 = luts[y1[:, None], x1[None, :], canal]

    out = (
        (1.0 - wy) * (1.0 - wx) * v00
        + (1.0 - wy) * wx * v01
        + wy * (1.0 - wx) * v10
        + wy * wx * v11
    )
    return np.clip(np.round(out), 0, 255).astype(np.uint8)


def apply_on_gray_or_lab(image, func_2d):
    """Apply a 2-D operator to a grayscale image, or to the L channel in Lab."""
    if image.ndim == 2:
        return func_2d(image)
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2Lab)
    lab[:, :, 0] = func_2d(lab[:, :, 0])
    return cv2.cvtColor(lab, cv2.COLOR_Lab2BGR)


def egalisationHistoGlobale(image) -> np.ndarray:
    """Global histogram equalisation (grayscale directly, colour on Lab L)."""
    return apply_on_gray_or_lab(image, egalisation_globale_canal)


def egalisationAHE(image, tile_grid=(8, 8)) -> np.ndarray:
    """Adaptive Histogram Equalisation (no clip limit), bilinear stitching."""
    return apply_on_gray_or_lab(
        image, lambda c: egalisation_locale_blocs(c, tile_grid, None)
    )


def egalisationCLAHE(image, tile_grid=(8, 8), clip_limit: float = 2.0) -> np.ndarray:
    """Contrast-Limited AHE: clips each tile histogram at ``clip_limit``.

    The clipping bounds the local amplification of noise while keeping the
    adaptivity of AHE — the same principle as ``cv2.createCLAHE``.
    """
    return apply_on_gray_or_lab(
        image, lambda c: egalisation_locale_blocs(c, tile_grid, clip_limit)
    )
