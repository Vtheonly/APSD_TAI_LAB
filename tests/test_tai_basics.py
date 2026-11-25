"""TP1 from-scratch basics: fixed thresholding and histograms."""

import cv2
import numpy as np
import pytest

from TAI.utils.basics import calcul_histogramme_perso, seuillage_fixe_perso


@pytest.mark.parametrize("seuil", [0, 80, 128, 200, 255])
def test_fixed_thresholding_matches_opencv(small_gray, seuil):
    _, cv_ref = cv2.threshold(small_gray, seuil, 255, cv2.THRESH_BINARY)
    out = seuillage_fixe_perso(small_gray, seuil)
    assert np.array_equal(out, cv_ref)


def test_fixed_thresholding_boundary_convention():
    """Exactly-at-threshold pixels must go BLACK (strict >)."""
    img = np.full((5, 5), 80, dtype=np.uint8)
    out = seuillage_fixe_perso(img, 80)
    assert np.all(out == 0)
    out2 = seuillage_fixe_perso(img, 79)
    assert np.all(out2 == 255)


def test_fixed_thresholding_constant_images():
    assert np.all(seuillage_fixe_perso(np.zeros((4, 4), np.uint8), 128) == 0)
    assert np.all(seuillage_fixe_perso(np.full((4, 4), 255, np.uint8), 128) == 255)


def test_histogram_matches_calc_hist_grayscale(cameraman):
    ref = cv2.calcHist([cameraman], [0], None, [256], [0, 256]).ravel()
    assert np.array_equal(calcul_histogramme_perso(cameraman), ref)


def test_histogram_matches_calc_hist_every_channel():
    img = np.array(
        [
            [[10, 200, 30], [40, 220, 50], [60, 240, 70]],
            [[80, 10, 90], [100, 30, 110], [120, 50, 130]],
            [[140, 70, 150], [160, 90, 170], [180, 110, 190]],
        ],
        dtype=np.uint8,
    )
    for ch in range(3):
        ref = cv2.calcHist([img], [ch], None, [256], [0, 256]).ravel()
        assert np.array_equal(calcul_histogramme_perso(img[:, :, ch]), ref)


def test_histogram_sums_to_pixel_count():
    rng = np.random.default_rng(9)
    img = rng.integers(0, 256, size=(37, 53), dtype=np.uint8)
    hist = calcul_histogramme_perso(img)
    assert hist.sum() == img.size
    assert hist.min() >= 0


def test_histogram_dtype_is_float32():
    img = np.full((3, 3), 7, dtype=np.uint8)
    hist = calcul_histogramme_perso(img)
    assert hist.dtype == np.float32
    assert hist[7] == 9
