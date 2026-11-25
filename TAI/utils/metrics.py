"""Unified image-quality metrics: PSNR and SSIM.

Convention (standardised across the whole TAI track)
----------------------------------------------------
``calculate_psnr`` returns ``float("inf")`` when ``MSE == 0`` (perfect
reconstruction). This is the mathematically correct limit of
``10*log10(255^2 / MSE)`` and lets callers detect identical images with
``math.isinf(psnr)``. Some earlier TAI labs returned ``100.0`` instead; the
unified convention documented here replaces those inconsistent variants.

SSIM follows Wang et al. (2004): an 11x11 Gaussian window (sigma = 1.5),
stabilising constants C1 = (0.01*L)^2 and C2 = (0.03*L)^2 with L = 255, and
channel-wise means for colour images.
"""

from __future__ import annotations

import math

import cv2
import numpy as np


def calculate_psnr(original_image, degraded_image, data_range: float = 255.0) -> float:
    """Peak Signal-to-Noise Ratio in decibels.

    PSNR = 10 * log10(data_range^2 / MSE)

    Returns ``float('inf')`` for identical inputs (MSE == 0).
    Matches ``cv2.PSNR`` (up to floating-point rounding) for finite values.
    """
    orig = np.asarray(original_image, dtype=np.float64)
    deg = np.asarray(degraded_image, dtype=np.float64)
    if orig.shape != deg.shape:
        raise ValueError(
            f"Image shapes differ: {orig.shape} vs {deg.shape} — PSNR undefined."
        )
    mse = float(np.mean((orig - deg) ** 2))
    if mse == 0.0:
        return float("inf")
    return 10.0 * math.log10((data_range**2) / mse)


def _ssim_gray(img1: np.ndarray, img2: np.ndarray, data_range: float) -> float:
    """SSIM between two single-channel images (Wang et al. 2004)."""
    a = img1.astype(np.float64)
    b = img2.astype(np.float64)
    c1 = (0.01 * data_range) ** 2
    c2 = (0.03 * data_range) ** 2

    mu1 = cv2.GaussianBlur(a, (11, 11), 1.5)
    mu2 = cv2.GaussianBlur(b, (11, 11), 1.5)
    mu1_sq, mu2_sq, mu1_mu2 = mu1 * mu1, mu2 * mu2, mu1 * mu2
    s1_sq = cv2.GaussianBlur(a * a, (11, 11), 1.5) - mu1_sq
    s2_sq = cv2.GaussianBlur(b * b, (11, 11), 1.5) - mu2_sq
    s12 = cv2.GaussianBlur(a * b, (11, 11), 1.5) - mu1_mu2

    num = (2.0 * mu1_mu2 + c1) * (2.0 * s12 + c2)
    den = (mu1_sq + mu2_sq + c1) * (s1_sq + s2_sq + c2)
    return float(np.mean(num / den))


def calculate_ssim(img1, img2, data_range: float = 255.0) -> float:
    """Structural Similarity Index (Wang et al. 2004), no external dependency.

    For colour images the SSIM is averaged over the B, G, R channels.
    Returns 1.0 for identical inputs.
    """
    a = np.asarray(img1)
    b = np.asarray(img2)
    if a.shape != b.shape:
        raise ValueError(
            f"Image shapes differ: {a.shape} vs {b.shape} — SSIM undefined."
        )
    if a.ndim == 3:
        return float(
            np.mean(
                [_ssim_gray(a[:, :, c], b[:, :, c], data_range) for c in range(a.shape[2])]
            )
        )
    return _ssim_gray(a, b, data_range)
