"""Deterministic noise generators shared by TP2_Exo1, TP2_Exo2 and TP2_Exo3.

Both generators are seeded by default (``seed=42``) so that every notebook
(and every pytest run) produces bit-identical noisy images — the three labs
share *one* canonical implementation instead of duplicated inline fallbacks.

* ``add_gaussian_noise`` — additive zero-mean white Gaussian noise.
  ``cv2.randn`` is driven by ``cv2.setRNGSeed(seed)`` for reproducibility.
* ``sp_noise``           — impulse ("salt & pepper") noise. A fresh
  ``numpy.random.default_rng(seed)`` decides which pixels become black or
  white; each of the two extremes covers ``prob/2`` of all pixels.
"""

from __future__ import annotations

import math

import cv2
import numpy as np


def add_gaussian_noise(image, variance: float, seed: int = 42) -> np.ndarray:
    """Add zero-mean Gaussian white noise of the given variance (sigma^2).

    The noisy image is clipped to [0, 255] and returned as ``uint8``.
    """
    sigma = math.sqrt(float(variance))
    noise = np.zeros(image.shape, dtype=np.float32)
    cv2.setRNGSeed(seed)
    cv2.randn(noise, 0.0, sigma)
    noisy = cv2.add(image.astype(np.float32), noise)
    return np.clip(noisy, 0, 255).astype(np.uint8)


def sp_noise(image, prob: float, seed: int = 42) -> np.ndarray:
    """Replace ~``prob`` of all pixels by pure black or pure white impulses.

    Grayscale and colour images are supported; for colour images every
    channel of an affected pixel is set to the extreme value. The remaining
    ``(1 - prob)`` pixels keep their original intensities exactly.
    """
    rng = np.random.default_rng(seed)
    output = image.copy()
    if image.ndim == 2:
        black, white = 0, 255
    elif image.shape[2] == 3:  # BGR
        black = np.array([0, 0, 0], dtype=np.uint8)
        white = np.array([255, 255, 255], dtype=np.uint8)
    else:  # BGRA
        black = np.array([0, 0, 0, 255], dtype=np.uint8)
        white = np.array([255, 255, 255, 255], dtype=np.uint8)
    probs = rng.random(output.shape[:2])
    output[probs < (prob / 2.0)] = black
    output[probs > 1.0 - (prob / 2.0)] = white
    return output
