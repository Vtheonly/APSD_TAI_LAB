"""Pytest configuration for the APSD_TAI_LAB test-suite.

Puts the repository root on ``sys.path`` (making the ``TAI.utils`` package
importable) and exposes shared fixtures used across the test modules.
"""

from pathlib import Path

import cv2
import pytest
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent

import sys

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def images_dir(repo_root) -> Path:
    d = repo_root / "TAI" / "images"
    if not d.is_dir():
        pytest.skip("TAI/images dataset not available")
    return d


@pytest.fixture(scope="session")
def cameraman(images_dir) -> np.ndarray:
    from TAI.utils.env_io import load_image

    return load_image("tp1_tp2_cameraman_gray.bmp", cv2.IMREAD_GRAYSCALE, images_dir=images_dir)


@pytest.fixture(scope="session")
def noisy_images(cameraman):
    """Deterministic (im1, im2 Gaussian var=100, im3 S&P p=0.10) triplet."""
    from TAI.utils.noise import add_gaussian_noise, sp_noise

    im2 = add_gaussian_noise(cameraman, variance=100.0, seed=42)
    im3 = sp_noise(cameraman, prob=0.10, seed=42)
    return cameraman, im2, im3


@pytest.fixture()
def small_gray():
    """A small deterministic grayscale image with an edge."""
    rng = np.random.default_rng(7)
    img = rng.integers(40, 90, size=(24, 24), dtype=np.uint8)
    img[:, 12:] = np.clip(img[:, 12:].astype(int) + 100, 0, 255).astype(np.uint8)
    return img


@pytest.fixture()
def small_binary():
    """A small deterministic binary mask (values in {0, 255})."""
    rng = np.random.default_rng(11)
    img = (rng.random((20, 20)) > 0.5).astype(np.uint8) * 255
    img[:4, :4] = 255  # solid corner block
    img[-4:, -4:] = 0
    return img
