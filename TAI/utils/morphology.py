"""From-scratch mathematical morphology, verified bit-for-bit against OpenCV.

Boundary handling (the key to matching OpenCV exactly)
------------------------------------------------------
Out-of-bounds pixels are padded with the *neutral element* of each operation
(the same convention as OpenCV's ``morphologyDefaultBorderValue``):

* **Erosion** pads with the maximum intensity (``255`` for uint8) so border
  pixels are never artificially eroded to 0.
* **Dilation** pads with ``0`` so border pixels are never artificially
  inflated.

Kernel reflection
-----------------
Dilation is defined over the *reflected* structuring element
``B_hat = B[::-1, ::-1]``; applying the reflection explicitly makes
``custom_dilate`` match ``cv2.dilate`` bit-for-bit even for asymmetric
kernels.
"""

from __future__ import annotations

import numpy as np


def _validate_kernel(kernel) -> np.ndarray:
    k = np.asarray(kernel)
    if k.ndim != 2 or k.shape[0] % 2 == 0 or k.shape[1] % 2 == 0:
        raise ValueError("Structuring element must be a 2D array with odd dimensions.")
    return k


def custom_erode(img, kernel) -> np.ndarray:
    """Morphological erosion with neutral max-value border padding.

    (I ⊖ B)(y, x) = min over active B offsets of I(y + dy, x + dx).
    """
    k = _validate_kernel(kernel)
    kh, kw = k.shape
    rh, rw = kh // 2, kw // 2
    h, w = img.shape
    max_val = 255 if img.dtype == np.uint8 else np.iinfo(img.dtype).max
    padded = np.pad(img, ((rh, rh), (rw, rw)), mode="constant", constant_values=max_val)
    out = np.full((h, w), max_val, dtype=img.dtype)
    for dy in range(kh):
        for dx in range(kw):
            if k[dy, dx] > 0:
                out = np.minimum(out, padded[dy:dy + h, dx:dx + w])
    return out


def custom_dilate(img, kernel) -> np.ndarray:
    """Morphological dilation with kernel reflection and 0 border padding.

    (I ⊕ B)(y, x) = max over active offsets of the reflected B.
    """
    k = _validate_kernel(kernel)[::-1, ::-1]
    kh, kw = k.shape
    rh, rw = kh // 2, kw // 2
    h, w = img.shape
    padded = np.pad(img, ((rh, rh), (rw, rw)), mode="constant", constant_values=0)
    out = np.zeros((h, w), dtype=img.dtype)
    for dy in range(kh):
        for dx in range(kw):
            if k[dy, dx] > 0:
                out = np.maximum(out, padded[dy:dy + h, dx:dx + w])
    return out


def custom_opening(img, kernel) -> np.ndarray:
    """Opening: erosion followed by dilation, (I ∘ B) = (I ⊖ B) ⊕ B."""
    return custom_dilate(custom_erode(img, kernel), kernel)


def custom_closing(img, kernel) -> np.ndarray:
    """Closing: dilation followed by erosion, (I • B) = (I ⊕ B) ⊖ B."""
    return custom_erode(custom_dilate(img, kernel), kernel)


def custom_erode_scalar_patch(patch, kernel) -> np.ndarray:
    """Explicit pixel-by-pixel scalar erosion for pedagogical verification.

    Used in the morphology notebook to prove that the vectorised offset
    slicing, the nested-loop traversal and OpenCV all agree bit-for-bit.
    """
    k = _validate_kernel(kernel)
    kh, kw = k.shape
    rh, rw = kh // 2, kw // 2
    h, w = patch.shape
    padded = np.pad(patch, ((rh, rh), (rw, rw)), mode="constant", constant_values=255)
    out = np.zeros_like(patch)
    active_offsets = [(dy, dx) for dy in range(kh) for dx in range(kw) if k[dy, dx] > 0]
    for y in range(h):
        for x in range(w):
            min_v = 255
            for dy, dx in active_offsets:
                val = int(padded[y + dy, x + dx])
                if val < min_v:
                    min_v = val
            out[y, x] = min_v
    return out


def custom_zhang_suen_thinning(binary_img):
    """Vectorised Zhang-Suen (1984) thinning algorithm.

    Iteratively peels border pixels through two alternating sub-iterations
    until only a 1-pixel-wide, topology-preserving skeleton remains.

    For each foreground pixel P1 with 8 neighbours P2..P9 (clockwise from
    top-left row), deletion requires:

    * 2 <= B(P1) <= 6  (not isolated, not a thick interior),
    * A(P1) == 1       (exactly one 0 -> 1 transition around the ring —
                        deletion preserves connectivity),
    * sub-iteration 1: P2*P4*P6 == 0 and P4*P6*P8 == 0 (south-east peel),
    * sub-iteration 2: P2*P4*P8 == 0 and P2*P6*P8 == 0 (north-west peel).

    Returns ``(skeleton, n_iterations)`` where the skeleton is 0/255 uint8.
    """
    img = (binary_img > 0).astype(np.uint8)
    iterations = 0
    while True:
        removed_any = False
        for sub_iter in (0, 1):
            p = np.pad(img, 1, mode="constant", constant_values=0)
            p2, p3, p4 = p[:-2, 1:-1], p[:-2, 2:], p[1:-1, 2:]
            p5, p6, p7 = p[2:, 2:], p[2:, 1:-1], p[2:, :-2]
            p8, p9 = p[1:-1, :-2], p[:-2, :-2]

            b = p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
            ring = [p2, p3, p4, p5, p6, p7, p8, p9, p2]
            a = np.zeros_like(img, dtype=np.uint8)
            for idx in range(8):
                a += ((ring[idx] == 0) & (ring[idx + 1] == 1)).astype(np.uint8)

            if sub_iter == 0:
                c1 = (p2 * p4 * p6) == 0
                c2 = (p4 * p6 * p8) == 0
            else:
                c1 = (p2 * p4 * p8) == 0
                c2 = (p2 * p6 * p8) == 0

            to_delete = (img == 1) & (b >= 2) & (b <= 6) & (a == 1) & c1 & c2
            if np.any(to_delete):
                img[to_delete] = 0
                removed_any = True
        iterations += 1
        if not removed_any:
            break
    return (img * 255).astype(np.uint8), iterations
