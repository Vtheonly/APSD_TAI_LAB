"""TP2 morphology: erode/dilate/open/close bit-for-bit vs OpenCV + Zhang-Suen."""

import cv2
import numpy as np
import pytest

from TAI.utils.morphology import (
    custom_closing,
    custom_dilate,
    custom_erode,
    custom_erode_scalar_patch,
    custom_opening,
    custom_zhang_suen_thinning,
)

RECT_KS = [
    np.ones((3, 3), np.uint8),
    np.ones((5, 5), np.uint8),
    np.ones((7, 7), np.uint8),
]
ELLIPSE_KS = [
    cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)),
    cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
]


@pytest.mark.parametrize("se", RECT_KS + ELLIPSE_KS, ids=lambda k: f"{k.shape[0]}x{k.shape[1]}-{k.sum()}")
def test_custom_erode_bit_for_bit_binary(small_binary, se):
    assert np.array_equal(custom_erode(small_binary, se), cv2.erode(small_binary, se))


@pytest.mark.parametrize("se", RECT_KS + ELLIPSE_KS, ids=lambda k: f"{k.shape[0]}x{k.shape[1]}-{k.sum()}")
def test_custom_dilate_bit_for_bit_binary(small_binary, se):
    assert np.array_equal(custom_dilate(small_binary, se), cv2.dilate(small_binary, se))


@pytest.mark.parametrize("se", RECT_KS + ELLIPSE_KS, ids=lambda k: f"{k.shape[0]}x{k.shape[1]}-{k.sum()}")
def test_custom_erode_bit_for_bit_grayscale(small_gray, se):
    assert np.array_equal(custom_erode(small_gray, se), cv2.erode(small_gray, se))


@pytest.mark.parametrize("se", RECT_KS + ELLIPSE_KS, ids=lambda k: f"{k.shape[0]}x{k.shape[1]}-{k.sum()}")
def test_custom_dilate_bit_for_bit_grayscale(small_gray, se):
    assert np.array_equal(custom_dilate(small_gray, se), cv2.dilate(small_gray, se))


@pytest.mark.parametrize("se", RECT_KS + ELLIPSE_KS, ids=lambda k: f"{k.shape[0]}x{k.shape[1]}-{k.sum()}")
def test_custom_opening_bit_for_bit(small_binary, small_gray, se):
    assert np.array_equal(custom_opening(small_binary, se), cv2.morphologyEx(small_binary, cv2.MORPH_OPEN, se))
    assert np.array_equal(custom_opening(small_gray, se), cv2.morphologyEx(small_gray, cv2.MORPH_OPEN, se))


@pytest.mark.parametrize("se", RECT_KS + ELLIPSE_KS, ids=lambda k: f"{k.shape[0]}x{k.shape[1]}-{k.sum()}")
def test_custom_closing_bit_for_bit(small_binary, small_gray, se):
    assert np.array_equal(custom_closing(small_binary, se), cv2.morphologyEx(small_binary, cv2.MORPH_CLOSE, se))
    assert np.array_equal(custom_closing(small_gray, se), cv2.morphologyEx(small_gray, cv2.MORPH_CLOSE, se))


def test_asymmetric_kernel_dilation_reflection():
    """Dilation must use the reflected kernel (asymmetric SE exposes it)."""
    se = np.array([[1, 0, 0], [0, 0, 0], [0, 0, 1]], np.uint8)
    img = np.zeros((11, 11), np.uint8)
    img[5, 5] = 255
    assert np.array_equal(custom_dilate(img, se), cv2.dilate(img, se))


def test_constant_images_are_fixed_points():
    img = np.full((10, 10), 128, np.uint8)
    k = np.ones((3, 3), np.uint8)
    assert np.all(custom_erode(img, k) == 128)
    assert np.all(custom_dilate(img, k) == 128)


def test_odd_kernel_validation():
    img = np.zeros((5, 5), np.uint8)
    for fn in (custom_erode, custom_dilate, custom_opening, custom_closing, custom_erode_scalar_patch):
        with pytest.raises(ValueError):
            fn(img, np.ones((2, 2), np.uint8))


def test_scalar_patch_equals_vectorized(small_binary):
    k = np.ones((3, 3), np.uint8)
    assert np.array_equal(custom_erode_scalar_patch(small_binary, k), custom_erode(small_binary, k))


def test_erode_shrinks_and_dilate_grows_foreground(small_binary):
    k = np.ones((5, 5), np.uint8)
    fg_before = np.mean(small_binary == 255)
    fg_erode = np.mean(custom_erode(small_binary, k) == 255)
    fg_dilate = np.mean(custom_dilate(small_binary, k) == 255)
    assert fg_erode < fg_before < fg_dilate


# ---------------------------------------------------------------------------
# Zhang-Suen thinning
# ---------------------------------------------------------------------------
def test_zhang_suen_output_is_thin_binary(small_binary):
    skel, iters = custom_zhang_suen_thinning(small_binary)
    assert iters >= 1
    assert set(np.unique(skel)) <= {0, 255}
    assert np.all(skel[small_binary == 0] == 0)  # skeleton stays inside foreground
    assert np.sum(skel > 0) < np.sum(small_binary > 0)  # strictly thinner


def test_zhang_suen_solid_square_shrinks_to_axis():
    img = np.zeros((21, 21), np.uint8)
    img[5:15, 5:15] = 255  # 10x10 solid square
    skel, _ = custom_zhang_suen_thinning(img)
    assert np.sum(skel > 0) <= 2 * 10  # a line/point, not a block


def test_zhang_suen_preserves_connectivity():
    """A horizontal bar must remain a connected 1-px line."""
    img = np.zeros((9, 25), np.uint8)
    img[4, 2:23] = 255
    skel, _ = custom_zhang_suen_thinning(img)
    n, labels = cv2.connectedComponents((skel > 0).astype(np.uint8))
    assert n - 1 == 1  # exactly one connected component
    assert np.sum(skel > 0) <= 25


@pytest.mark.skipif(not hasattr(cv2, "ximgproc"), reason="opencv-contrib required")
def test_zhang_suen_close_to_cv2_ximgproc():
    """Custom vs OpenCV Zhang-Suen: identical or near-identical (tie-order)."""
    img = np.zeros((31, 31), np.uint8)
    img[6:24, 6:24] = 255
    img[3, 3] = 255
    img[27, 28] = 255
    skel, _ = custom_zhang_suen_thinning(img)
    ref = cv2.ximgproc.thinning(img, thinningType=cv2.ximgproc.THINNING_ZHANGSUEN)
    # Border/tie-breaking order may differ slightly -> allow small mismatch
    diff = np.sum(skel != ref)
    assert diff <= 0.05 * max(1, np.sum(ref > 0) + np.sum(skel > 0))
