"""TP2 contrast: expansion, global/AHE/CLAHE equalization."""

import cv2
import numpy as np
import pytest

from TAI.utils.contrast import (
    apply_on_gray_or_lab,
    egalisationAHE,
    egalisationCLAHE,
    egalisationHistoGlobale,
    egalisation_locale_blocs,
    expansionHisto,
)


# ---------------------------------------------------------------------------
# expansionHisto
# ---------------------------------------------------------------------------
def test_expansion_matches_cv2_normalize(cameraman):
    ref = cv2.normalize(cameraman, None, 0, 255, cv2.NORM_MINMAX)
    assert np.array_equal(expansionHisto(cameraman), ref)


def test_expansion_color_matches_cv2_normalize():
    rng = np.random.default_rng(6)
    img = rng.integers(30, 120, size=(32, 32, 3), dtype=np.uint8)
    ref = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)
    assert np.array_equal(expansionHisto(img), ref)


def test_expansion_stretches_range():
    img = np.full((16, 16), 100, dtype=np.uint8)
    img[:8] = 60
    out = expansionHisto(img)
    assert int(out.min()) == 0
    assert int(out.max()) == 255


def test_expansion_constant_image_returns_ymin():
    const = np.full((8, 8), 42, dtype=np.uint8)
    out = expansionHisto(const, seuil=0, Ymin=0, Ymax=255)
    assert np.all(out == 0)


def test_expansion_custom_output_range():
    rng = np.random.default_rng(1)
    img = rng.integers(10, 90, size=(12, 12), dtype=np.uint8)
    out = expansionHisto(img, seuil=0, Ymin=30, Ymax=200)
    assert int(out.min()) >= 30
    assert int(out.max()) <= 200


# ---------------------------------------------------------------------------
# egalisationHistoGlobale
# ---------------------------------------------------------------------------
def test_global_equalization_matches_cv2_equalizehist(cameraman):
    assert np.array_equal(egalisationHistoGlobale(cameraman), cv2.equalizeHist(cameraman))


def test_global_equalization_constant_image_unchanged():
    const = np.full((10, 10), 77, dtype=np.uint8)
    assert np.array_equal(egalisationHistoGlobale(const), const)


def test_global_equalization_increases_contrast():
    img = np.tile(np.linspace(90, 110, 20, dtype=np.uint8), (20, 1))
    out = egalisationHistoGlobale(img)
    assert int(out.std()) > 2 * int(img.std())


# ---------------------------------------------------------------------------
# AHE / CLAHE
# ---------------------------------------------------------------------------
def test_ahe_and_clahe_shapes_and_range(cameraman):
    for out in (egalisationAHE(cameraman), egalisationCLAHE(cameraman)):
        assert out.shape == cameraman.shape
        assert out.dtype == np.uint8
        assert 0 <= int(out.min()) and int(out.max()) <= 255


def test_clahe_improves_local_contrast_on_low_contrast_image():
    rng = np.random.default_rng(0)
    img = rng.integers(110, 140, size=(64, 64), dtype=np.uint8)
    out = egalisationCLAHE(img)
    assert int(out.std()) > 2 * int(img.std())


def test_ahe_clip_limit_changes_output():
    img = np.tile(np.linspace(110, 150, 64, dtype=np.uint8), (64, 1))
    ahe = egalisation_locale_blocs(img, (8, 8), None)
    clahe = egalisation_locale_blocs(img, (8, 8), 2.0)
    assert not np.array_equal(ahe, clahe)


def test_color_images_processed_via_lab_l_channel():
    rng = np.random.default_rng(2)
    img = rng.integers(60, 100, size=(32, 32, 3), dtype=np.uint8)
    out = egalisationCLAHE(img)
    assert out.shape == img.shape
    # chrominance channels (a, b) must be untouched: round-trip difference
    # must live only in luminance
    lab_in = cv2.cvtColor(img, cv2.COLOR_BGR2Lab)
    lab_out = cv2.cvtColor(out, cv2.COLOR_BGR2Lab)
    assert np.max(np.abs(lab_in[:, :, 1].astype(int) - lab_out[:, :, 1].astype(int))) <= 2
    assert np.max(np.abs(lab_in[:, :, 2].astype(int) - lab_out[:, :, 2].astype(int))) <= 2
    assert lab_out[:, :, 0].std() > lab_in[:, :, 0].std()  # L was equalized


def test_apply_on_gray_or_lab_passthrough_gray(small_gray):
    identity = apply_on_gray_or_lab(small_gray, lambda c: c)
    assert np.array_equal(identity, small_gray)
