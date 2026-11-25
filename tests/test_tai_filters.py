"""TP2 spatial filters: mean (3 variants), median, bilateral, adaptive, Nagao."""

import time

import cv2
import numpy as np
import pytest

from TAI.utils.filters import (
    build_nagao_masks,
    filtreMedian,
    filtreMoyenne,
    filtreMoyenneAdaptative,
    filtreMoyenneAdaptative_MMSE,
    filtreMoyenne_integrale,
    filtreMoyenne_naif_boucles,
    filtreMoyenne_separable,
    filtreNagao,
    filtrebilateral,
)


# ---------------------------------------------------------------------------
# filtreMoyenne vs cv2.blur
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("k", [3, 5, 7])
def test_filtreMoyenne_matches_cv2_blur_interior(noisy_images, k):
    """Custom mean filter equals cv2.blur on the image interior."""
    _, im2, _ = noisy_images
    cv_out = cv2.blur(im2, (k, k))
    my_out = filtreMoyenne(im2, k)
    r = k // 2
    assert np.array_equal(cv_out[r:-r, r:-r], my_out[r:-r, r:-r])


@pytest.mark.parametrize("fn", [filtreMoyenne, filtreMoyenne_separable,
                                filtreMoyenne_integrale, filtreMedian,
                                filtrebilateral, filtreMoyenneAdaptative,
                                filtreMoyenneAdaptative_MMSE])
def test_odd_kernel_validation(fn, small_gray):
    with pytest.raises(ValueError):
        if fn is filtrebilateral:
            fn(small_gray, 4, 2.0, 40.0)
        else:
            fn(small_gray, 4)


def test_filtreMoyenne_constant_image_is_identity():
    const = np.full((16, 16), 77, dtype=np.uint8)
    assert np.all(filtreMoyenne(const, 3) == 77)
    assert np.all(filtreMoyenne_separable(const, 5) == 77)
    assert np.all(filtreMoyenne_integrale(const, 7) == 77)


def test_filtreMoyenne_variants_agree():
    """Naive / separable / integral / vectorised must produce identical values."""
    rng = np.random.default_rng(4)
    img = rng.integers(0, 256, size=(30, 30), dtype=np.uint8)
    for k in (3, 5, 9):
        a = filtreMoyenne_naif_boucles(img, k)
        b = filtreMoyenne_separable(img, k)
        c = filtreMoyenne_integrale(img, k)
        d = filtreMoyenne(img, k)
        assert np.max(np.abs(a.astype(int) - b.astype(int))) <= 1
        assert np.max(np.abs(a.astype(int) - c.astype(int))) <= 1
        assert np.max(np.abs(a.astype(int) - d.astype(int))) <= 1


def test_integral_filter_is_faster_than_naive_for_large_k():
    rng = np.random.default_rng(8)
    img = rng.integers(0, 256, size=(64, 64), dtype=np.uint8)
    k = 21
    t0 = time.perf_counter()
    filtreMoyenne_naif_boucles(img, k)
    t_naive = time.perf_counter() - t0
    t0 = time.perf_counter()
    filtreMoyenne_integrale(img, k)
    t_int = time.perf_counter() - t0
    assert t_int < t_naive  # O(1)/pixel must beat O(k^2)/pixel


# ---------------------------------------------------------------------------
# filtreMedian
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("k", [3, 5])
def test_filtreMedian_matches_cv2_median(noisy_images, k):
    _, _, im3 = noisy_images
    cv_out = cv2.medianBlur(im3, k)
    my_out = filtreMedian(im3, k)
    r = k // 2
    assert np.array_equal(cv_out[r:-r, r:-r], my_out[r:-r, r:-r])


def test_filtreMedian_removes_isolated_impulses():
    """A single S&P pixel in a flat region must be completely removed."""
    img = np.full((15, 15), 100, dtype=np.uint8)
    img[7, 7] = 255
    img[3, 11] = 0
    out = filtreMedian(img, 3)
    assert out[7, 7] == 100
    assert out[3, 11] == 100


def test_filtreMedian_constant_image_is_identity():
    const = np.full((12, 12), 33, dtype=np.uint8)
    assert np.all(filtreMedian(const, 3) == 33)


# ---------------------------------------------------------------------------
# filtrebilateral
# ---------------------------------------------------------------------------
def test_filtrebilateral_flat_region_smoothed_edge_preserved():
    img = np.full((20, 20), 90, dtype=np.uint8)
    img[:, 10:] = 190
    out = filtrebilateral(img, 7, sigma_s=2.0, sigma_r=40.0)
    # edge must stay razor sharp with a small sigma_r
    assert abs(int(out[10, 9]) - int(out[10, 10])) > 50
    # flat areas must be preserved exactly (all neighbors identical)
    assert np.all(out[:, :6] == 90)


def test_filtrebilateral_reduces_gaussian_noise(noisy_images):
    from TAI.utils.metrics import calculate_psnr

    im1, im2, _ = noisy_images
    out = filtrebilateral(im2, 7, sigma_s=2.0, sigma_r=40.0)
    assert calculate_psnr(im1, out) > calculate_psnr(im1, im2)


# ---------------------------------------------------------------------------
# adaptive filters
# ---------------------------------------------------------------------------
def test_filtreMoyenneAdaptative_preserves_strong_edges():
    img = np.full((30, 30), 60, dtype=np.uint8)
    img[:, 15:] = 200  # step edge of 140 > seuil=30
    out = filtreMoyenneAdaptative(img, k=5, seuil=30.0)
    assert abs(int(out[15, 14]) - int(out[15, 15])) > 100


def test_filtreMoyenneAdaptative_robust_variant_removes_impulse():
    img = np.full((15, 15), 100, dtype=np.uint8)
    img[7, 7] = 255  # isolated impulse
    out = filtreMoyenneAdaptative(img, k=5, seuil=30.0, robust_impulsion=True)
    assert out[7, 7] == 100


def test_filtreMoyenneAdaptative_MMSE_improves_psnr(noisy_images):
    from TAI.utils.metrics import calculate_psnr

    im1, im2, _ = noisy_images
    out = filtreMoyenneAdaptative_MMSE(im2, k=5, noise_var=100.0)
    assert calculate_psnr(im1, out) > calculate_psnr(im1, im2)


def test_filtreMoyenneAdaptative_constant_image_is_identity():
    const = np.full((12, 12), 50, dtype=np.uint8)
    assert np.all(filtreMoyenneAdaptative(const, 5, 30.0) == 50)


# ---------------------------------------------------------------------------
# Nagao
# ---------------------------------------------------------------------------
def test_build_nagao_masks_structure():
    for k in (5, 7, 9):
        masks = build_nagao_masks(k)
        assert len(masks) == 9
        for m in masks:
            assert m.shape == (k, k)
            assert m.sum() > 0
    with pytest.raises(ValueError):
        build_nagao_masks(4)
    with pytest.raises(ValueError):
        build_nagao_masks(3)


def test_filtreNagao_flat_region_is_identity():
    const = np.full((20, 20), 88, dtype=np.uint8)
    out = filtreNagao(const, 5)
    assert np.all(out == 88)


def test_filtreNagao_preserves_step_edge():
    img = np.full((40, 40), 70, dtype=np.uint8)
    img[:, 20:] = 180
    out = filtreNagao(img, 5)
    # a strong edge must survive Nagao smoothing
    assert abs(int(out[20, 19]) - int(out[20, 20])) > 50


def test_filtreNagao_improves_psnr_over_noise_on_flat_plus_edge_scene():
    """On a flat-regions-plus-step-edge scene, Nagao clearly beats the noise.

    (On heavily textured natural images such as Cameraman, the edge-preserving
    bias can outweigh the variance reduction and PSNR may drop — the visual
    quality still improves; that behaviour is asserted in the notebook.)
    """
    from TAI.utils.metrics import calculate_psnr
    from TAI.utils.noise import add_gaussian_noise

    scene = np.full((48, 48), 100, dtype=np.uint8)
    scene[:, 24:] = 160
    noisy = add_gaussian_noise(scene, variance=100.0, seed=1)
    out = filtreNagao(noisy, 5)
    assert calculate_psnr(scene, out) > calculate_psnr(scene, noisy)


def test_filtreNagao_iterations_smooth_more():
    rng = np.random.default_rng(2)
    img = rng.integers(0, 256, size=(32, 32), dtype=np.uint8)
    out1 = filtreNagao(img, 5, iterations=1)
    out3 = filtreNagao(img, 5, iterations=3)
    assert not np.array_equal(out1, out3)
    # repeated application flattens more (lower variance relative to out1)
    var1 = np.var(out1.astype(float))
    var3 = np.var(out3.astype(float))
    assert var3 <= var1 * 1.05
