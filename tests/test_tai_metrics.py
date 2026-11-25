"""TAI.utils.metrics — PSNR and SSIM tests."""

import math

import cv2
import numpy as np
import pytest

from TAI.utils.metrics import calculate_psnr, calculate_ssim


def test_psnr_identical_images_is_infinity(cameraman):
    assert calculate_psnr(cameraman, cameraman) == float("inf")


def test_psnr_matches_cv2_psnr(cameraman, noisy_images):
    _, im2, im3 = noisy_images
    for degraded in (im2, im3):
        assert math.isclose(calculate_psnr(cameraman, degraded), cv2.PSNR(cameraman, degraded), rel_tol=1e-9)


def test_psnr_known_value():
    """MSE = 100 (every pixel off by 10) -> PSNR = 10*log10(255^2/100)."""
    a = np.full((10, 10), 100, dtype=np.uint8)
    b = np.full((10, 10), 110, dtype=np.uint8)
    expected = 10.0 * math.log10(255.0**2 / 100.0)
    assert math.isclose(calculate_psnr(a, b), expected, rel_tol=1e-9)


def test_psnr_gaussian_noise_close_to_theory(cameraman, noisy_images):
    _, im2, _ = noisy_images  # variance 100 -> expected ~28.13 dB
    assert abs(calculate_psnr(cameraman, im2) - 10 * math.log10(255.0**2 / 100.0)) < 0.5


def test_psnr_shape_mismatch_raises(small_gray):
    with pytest.raises(ValueError):
        calculate_psnr(small_gray, small_gray[:4, :4])


def test_psnr_is_symmetric(cameraman, noisy_images):
    _, im2, _ = noisy_images
    assert math.isclose(calculate_psnr(cameraman, im2), calculate_psnr(im2, cameraman), rel_tol=1e-9)


def test_ssim_identical_images_is_one(cameraman):
    assert calculate_ssim(cameraman, cameraman) == pytest.approx(1.0, abs=1e-9)


def test_ssim_decreases_with_noise(cameraman, noisy_images):
    _, im2, im3 = noisy_images
    s_clean = calculate_ssim(cameraman, cameraman)
    s_gauss = calculate_ssim(cameraman, im2)
    s_sp = calculate_ssim(cameraman, im3)
    assert s_clean > s_gauss > s_sp > 0


def test_ssim_grayscale_and_color():
    rng = np.random.default_rng(3)
    gray = rng.integers(0, 256, size=(64, 64), dtype=np.uint8)
    shifted = np.clip(gray.astype(int) + 20, 0, 255).astype(np.uint8)
    color = cv2.cvtColor(shifted, cv2.COLOR_GRAY2BGR)
    assert 0.0 < calculate_ssim(gray, shifted) < 1.0
    assert 0.0 < calculate_ssim(color, color.copy()) == pytest.approx(1.0, abs=1e-9)
    assert 0.0 < calculate_ssim(color, cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)) < 1.0


def test_ssim_shape_mismatch_raises(small_gray):
    with pytest.raises(ValueError):
        calculate_ssim(small_gray, small_gray[:4, :4])
