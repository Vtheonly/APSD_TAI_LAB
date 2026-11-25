"""TP2 spatial filters — from-scratch implementations verified against OpenCV.

All filters operate on single-channel 8-bit images and share these rules:

* the window size must be **odd** (``ValueError`` otherwise),
* boundary handling uses edge-replicating or reflecting padding that mirrors
  OpenCV's default behaviour closely enough for bit-exact comparisons on the
  image interior,
* results are rounded and clipped back to ``uint8`` in ``[0, 255]``.

Functions
---------
filtreMoyenne              box (mean) filter, O(k^2) vectorised sliding sum.
filtreMoyenne_naif_boucles pedagogical nested-loop reference (slow).
filtreMoyenne_separable    separable 1D horizontal + vertical passes, O(2k).
filtreMoyenne_integrale    summed-area table (integral image), O(1)/pixel.
filtreMedian               median filter via sliding-window views.
filtrebilateral            bilateral filter (spatial + range Gaussians).
filtreMoyenneAdaptative    adaptive mean (course formula, optional impulse-
                            robust median fallback).
filtreMoyenneAdaptative_MMSE  local MMSE / Lee adaptive filter.
build_nagao_masks / filtreNagao  Nagao edge-preserving adaptive filter.
"""

from __future__ import annotations

import math

import cv2
import numpy as np


# ---------------------------------------------------------------------------
# Box (mean) filters
# ---------------------------------------------------------------------------
def _validate_odd(k: int) -> None:
    if k % 2 == 0:
        raise ValueError(f"Window size must be odd, got {k}.")


def filtreMoyenne(image, taille_fenetre: int) -> np.ndarray:
    """Box filter: each output pixel is the mean of its k x k neighbourhood.

    Complexity O(H*W*k^2) using k^2 shifted-array accumulations.
    """
    _validate_odd(taille_fenetre)
    r = taille_fenetre // 2
    padded = np.pad(image.astype(np.float64), r, mode="reflect")
    h, w = image.shape
    acc = np.zeros((h, w), dtype=np.float64)
    for dy in range(taille_fenetre):
        for dx in range(taille_fenetre):
            acc += padded[dy:dy + h, dx:dx + w]
    return np.clip(np.round(acc / (taille_fenetre * taille_fenetre)), 0, 255).astype(np.uint8)


def filtreMoyenne_naif_boucles(image, k: int) -> np.ndarray:
    """Explicit nested-loop mean filter (the O(H*W*k^2) naive baseline)."""
    _validate_odd(k)
    r = k // 2
    h, w = image.shape
    padded = np.pad(image.astype(np.float64), r, mode="reflect")
    out = np.zeros((h, w), dtype=np.uint8)
    area = float(k * k)
    for i in range(h):
        for j in range(w):
            out[i, j] = int(round(np.sum(padded[i:i + k, j:j + k]) / area))
    return out


def filtreMoyenne_separable(image, k: int) -> np.ndarray:
    """Separable mean filter: 1D horizontal pass then 1D vertical pass.

    Exploits the rank-1 structure of the box kernel to reach O(H*W*2k).
    """
    _validate_odd(k)
    r = k // 2
    h, w = image.shape
    padded = np.pad(image.astype(np.float64), r, mode="reflect")
    # Horizontal 1D pass
    horiz = np.zeros((h + 2 * r, w), dtype=np.float64)
    for dx in range(k):
        horiz += padded[:, dx:dx + w]
    horiz /= k
    # Vertical 1D pass
    vert = np.zeros((h, w), dtype=np.float64)
    for dy in range(k):
        vert += horiz[dy:dy + h, :]
    vert /= k
    return np.clip(np.round(vert), 0, 255).astype(np.uint8)


def filtreMoyenne_integrale(image, k: int) -> np.ndarray:
    """Summed-area-table mean filter — 4 table lookups per pixel, O(1)/pixel.

    The integral image (SAT) stores cumulative sums so that any rectangular
    window sum reduces to ``SAT(br) - SAT(tl) + corner corrections``.
    """
    _validate_odd(k)
    r = k // 2
    h, w = image.shape
    padded = np.pad(image.astype(np.float64), r, mode="reflect")
    sat = np.zeros((padded.shape[0] + 1, padded.shape[1] + 1), dtype=np.float64)
    sat[1:, 1:] = np.cumsum(np.cumsum(padded, axis=0), axis=1)
    sums = sat[k:, k:] - sat[:-k, k:] - sat[k:, :-k] + sat[:-k, :-k]
    return np.clip(np.round(sums / (k * k)), 0, 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# Median / bilateral filters
# ---------------------------------------------------------------------------
def filtreMedian(image, taille_fenetre: int) -> np.ndarray:
    """Median filter: replaces each pixel by the median of its k x k window.

    Median filtering is the reference remedy against impulse (salt & pepper)
    noise because an isolated extreme value never survives as the median.
    """
    _validate_odd(taille_fenetre)
    r = taille_fenetre // 2
    padded = np.pad(image, r, mode="edge")
    windows = np.lib.stride_tricks.sliding_window_view(
        padded, (taille_fenetre, taille_fenetre)
    )
    return np.median(windows, axis=(-2, -1)).astype(np.uint8)


def filtrebilateral(image, taille_fenetre: int, sigma_s: float, sigma_r: float) -> np.ndarray:
    """Bilateral filter: Gaussian-weighted mean in *both* space and intensity.

    w(p, q) = exp(-||p - q||^2 / (2 sigma_s^2)) * exp(-(I(p) - I(q))^2 / (2 sigma_r^2))

    The range term keeps strong edges sharp (large intensity differences get
    near-zero weight) while flat regions are smoothed like a Gaussian blur.
    """
    _validate_odd(taille_fenetre)
    r = taille_fenetre // 2
    h, w = image.shape
    img_f = image.astype(np.float64)
    padded = np.pad(img_f, r, mode="reflect")
    sum_weights = np.zeros((h, w), dtype=np.float64)
    sum_values = np.zeros((h, w), dtype=np.float64)
    inv_2s2 = -1.0 / (2.0 * sigma_s * sigma_s)
    inv_2r2 = -1.0 / (2.0 * sigma_r * sigma_r)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            neighbor = padded[r + dy:r + dy + h, r + dx:r + dx + w]
            spatial_w = math.exp((dy * dy + dx * dx) * inv_2s2)
            color_diff = neighbor - img_f
            color_w = np.exp((color_diff * color_diff) * inv_2r2)
            w_tot = spatial_w * color_w
            sum_weights += w_tot
            sum_values += w_tot * neighbor
    return np.clip(
        np.round(sum_values / np.maximum(sum_weights, 1e-12)), 0, 255
    ).astype(np.uint8)


# ---------------------------------------------------------------------------
# Adaptive filters (Devoir note b)
# ---------------------------------------------------------------------------
def filtreMoyenneAdaptative(image, k: int = 5, seuil: float = 30.0,
                            robust_impulsion: bool = False) -> np.ndarray:
    """Adaptive mean filter (course slide 42).

    C[i, j] = sum_k w(|a_k - A[i, j]|) * a_k / sum_k w(|a_k - A[i, j]|)
    with w(x) = 1 if |x| <= t else 0 — i.e. the mean of only those
    neighbours whose intensity stays within ``seuil`` of the centre pixel.

    With ``robust_impulsion=True``, when the central pixel is isolated (fewer
    than ~3 similar neighbours — the typical salt & pepper signature) the
    local median is substituted instead of the weighted mean.
    """
    _validate_odd(k)
    r = k // 2
    center = image.astype(np.float64)
    padded = np.pad(center, r, mode="reflect")
    windows = np.lib.stride_tricks.sliding_window_view(padded, (k, k))
    diffs = np.abs(windows - center[:, :, None, None])
    weights = (diffs <= seuil).astype(np.float64)
    sum_w = np.sum(weights, axis=(-2, -1))
    sum_val = np.sum(weights * windows, axis=(-2, -1))
    out = sum_val / np.maximum(sum_w, 1.0)
    if robust_impulsion:
        isolated = sum_w <= 2.0
        if np.any(isolated):
            med = np.median(windows, axis=(-2, -1))
            out = np.where(isolated, med, out)
    return np.clip(np.round(out), 0, 255).astype(np.uint8)


def filtreMoyenneAdaptative_MMSE(image, k: int = 5, noise_var: float = 100.0) -> np.ndarray:
    """Local MMSE (Lee) adaptive filter for additive Gaussian noise.

    The smoothing gain adapts per pixel to the ratio between the noise
    variance sigma_n^2 and the local signal variance sigma_L^2:

    C = A - (sigma_n^2 / max(sigma_L^2, sigma_n^2)) * (A - local_mean)

    Flat regions (sigma_L^2 small) are smoothed hard; textured or edged
    regions (sigma_L^2 large) keep the observed pixel nearly unchanged.
    """
    _validate_odd(k)
    r = k // 2
    img_f = image.astype(np.float64)
    padded = np.pad(img_f, r, mode="reflect")
    windows = np.lib.stride_tricks.sliding_window_view(padded, (k, k))
    local_mean = np.mean(windows, axis=(-2, -1))
    local_var = np.var(windows, axis=(-2, -1))
    gain = np.clip(noise_var / np.maximum(local_var, noise_var), 0.0, 1.0)
    out = img_f - gain * (img_f - local_mean)
    return np.clip(np.round(out), 0, 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# Nagao adaptive filter
# ---------------------------------------------------------------------------
def build_nagao_masks(taille_filtre: int) -> list:
    """Build the 9 Nagao sub-region masks (centre, 4 cardinals, 4 diagonals).

    Each mask is a ``taille x taille`` binary weight map over the window.
    """
    if taille_filtre < 5 or taille_filtre % 2 == 0:
        raise ValueError("Nagao filter size must be odd and >= 5.")
    r = taille_filtre // 2
    c = r  # centre index inside the k x k window
    masks = []

    # 1) central mask (3x3 for 5x5/7x7, larger for 9x9+)
    kc = 1 if r <= 3 else r // 2
    m_center = np.zeros((taille_filtre, taille_filtre), dtype=np.float64)
    m_center[c - kc:c + kc + 1, c - kc:c + kc + 1] = 1.0
    masks.append(m_center)

    # 2) North mask (+ 90/180/270-degree rotations -> West, South, East)
    m_north = np.zeros((taille_filtre, taille_filtre), dtype=np.float64)
    m_north[c, c] = 1.0
    for dr in range(1, r + 1):
        half_w = min(dr, max(1, r - 1))
        m_north[c - dr, c - half_w:c + half_w + 1] = 1.0
    for rot in range(4):
        masks.append(np.rot90(m_north, k=rot))

    # 3) North-West mask (+ rotations -> SW, SE, NE)
    m_nw = np.zeros((taille_filtre, taille_filtre), dtype=np.float64)
    m_nw[c, c] = 1.0
    m_nw[c - 1, c] = 1.0
    m_nw[c, c - 1] = 1.0
    m_nw[0:c, 0:c] = 1.0
    for rot in range(4):
        masks.append(np.rot90(m_nw, k=rot))

    return masks


def filtreNagao(im, taille_filtre: int = 5, iterations: int = 1) -> np.ndarray:
    """Nagao edge-preserving adaptive filter.

    The k x k window around each pixel is split into 9 overlapping
    sub-regions; the pixel is replaced by the mean of the sub-region with the
    **lowest variance**. Homogeneous regions get smoothed while edges stay
    crisp because any clique straddling an edge has a large variance.

    The implementation is fully vectorised: every clique's mean and variance
    are computed with ``cv2.filter2D`` on the image and its square, then the
    winning clique is selected per pixel with ``argmin``.
    """
    masks = build_nagao_masks(taille_filtre)
    current = im.astype(np.float64)
    for _ in range(iterations):
        img_sq = current * current
        means, variances = [], []
        for mask in masks:
            kernel = mask / np.sum(mask)
            mean = cv2.filter2D(current, cv2.CV_64F, kernel, borderType=cv2.BORDER_REFLECT)
            mean_sq = cv2.filter2D(img_sq, cv2.CV_64F, kernel, borderType=cv2.BORDER_REFLECT)
            var = np.maximum(0.0, mean_sq - mean * mean)
            means.append(mean)
            variances.append(var)
        means_stack = np.stack(means, axis=0)
        vars_stack = np.stack(variances, axis=0)
        best_idx = np.argmin(vars_stack, axis=0)
        current = np.take_along_axis(means_stack, best_idx[None, :, :], axis=0)[0]
    return np.clip(np.round(current), 0, 255).astype(np.uint8)
