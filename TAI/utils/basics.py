"""TP1 from-scratch basics: fixed thresholding and intensity histograms.

These deliberately use explicit per-pixel loops so the underlying algorithms
remain visible; they are verified bit-for-bit against their OpenCV
counterparts (``cv2.threshold`` with ``THRESH_BINARY`` and ``cv2.calcHist``)
in the TP1 notebooks and in ``tests/test_tai_basics.py``.
"""

from __future__ import annotations

import numpy as np


def seuillage_fixe_perso(image, seuil: int = 80):
    """Fixed (global) thresholding, from scratch.

    Every pixel with gray level strictly greater than ``seuil`` becomes 255
    (white); every pixel <= ``seuil`` becomes 0 (black) — exactly matching
    ``cv2.threshold(img, seuil, 255, cv2.THRESH_BINARY)``.
    """
    h, w = image.shape
    out = np.zeros((h, w), dtype=np.uint8)
    for y in range(h):
        for x in range(w):
            if image[y, x] > seuil:
                out[y, x] = 255
            else:
                out[y, x] = 0
    return out


def calcul_histogramme_perso(canal_2d):
    """256-bin intensity histogram of a single-channel image, from scratch.

    Returns a ``float32`` array of length 256 where bin *k* counts the pixels
    with intensity *k* — identical to
    ``cv2.calcHist([img], [0], None, [256], [0, 256]).ravel()``.
    """
    hist = np.zeros(256, dtype=np.float32)
    h, w = canal_2d.shape
    for y in range(h):
        for x in range(w):
            hist[canal_2d[y, x]] += 1.0
    return hist
