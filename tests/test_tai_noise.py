"""TAI.utils.noise — deterministic noise generator tests."""

import numpy as np
import pytest

from TAI.utils.noise import add_gaussian_noise, sp_noise


def test_gaussian_noise_deterministic(cameraman):
    a = add_gaussian_noise(cameraman, 100.0, seed=42)
    b = add_gaussian_noise(cameraman, 100.0, seed=42)
    c = add_gaussian_noise(cameraman, 100.0, seed=7)
    assert np.array_equal(a, b)
    assert not np.array_equal(a, c)


def test_gaussian_noise_statistics(cameraman):
    """Empirical variance of (noisy - original) should approximate sigma^2."""
    var = 400.0
    noisy = add_gaussian_noise(cameraman, var, seed=42).astype(np.float64)
    diff = noisy - cameraman.astype(np.float64)
    # clipping at 0/255 biases the variance slightly -> generous tolerance
    assert abs(diff.var() - var) < 0.25 * var
    assert abs(diff.mean()) < 10.0  # zero-mean noise


def test_gaussian_noise_preserves_shape_and_dtype(cameraman):
    noisy = add_gaussian_noise(cameraman, 100.0)
    assert noisy.shape == cameraman.shape
    assert noisy.dtype == np.uint8


def test_gaussian_noise_constant_image():
    const = np.full((32, 32), 128, dtype=np.uint8)
    noisy = add_gaussian_noise(const, 900.0, seed=42)
    assert noisy.shape == const.shape
    assert noisy.std() > 10  # sigma = 30


def test_sp_noise_deterministic(cameraman):
    a = sp_noise(cameraman, 0.10, seed=42)
    b = sp_noise(cameraman, 0.10, seed=42)
    assert np.array_equal(a, b)


def test_sp_noise_affected_ratio(cameraman):
    p = 0.10
    noisy = sp_noise(cameraman, p, seed=42)
    changed = np.mean(noisy != cameraman)
    # Each of black/white covers p/2 -> total ~ p (binomial tolerance)
    assert abs(changed - p) < 0.02


def test_sp_noise_values_are_extremes_or_original(cameraman):
    p = 0.25
    noisy = sp_noise(cameraman, p, seed=1)
    changed_mask = noisy != cameraman
    assert np.all((noisy[changed_mask] == 0) | (noisy[changed_mask] == 255))
    assert np.array_equal(noisy[~changed_mask], cameraman[~changed_mask])


def test_sp_noise_color_image():
    rng = np.random.default_rng(5)
    color = rng.integers(0, 256, size=(32, 32, 3), dtype=np.uint8)
    noisy = sp_noise(color, 0.2, seed=42)
    assert noisy.shape == color.shape
    changed = np.any(noisy != color, axis=2)
    assert abs(changed.mean() - 0.2) < 0.05
    # affected pixels must be pure black or pure white in all channels
    assert np.all(np.logical_or(noisy[changed].max(axis=1) == 0, noisy[changed].min(axis=1) == 255))


def test_sp_noise_zero_probability_is_identity(cameraman):
    assert np.array_equal(sp_noise(cameraman, 0.0, seed=42), cameraman)
