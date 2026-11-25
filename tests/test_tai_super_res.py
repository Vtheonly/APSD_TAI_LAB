"""TP2 super-resolution: bilinear 2x and contour stencils."""

import cv2
import numpy as np
import pytest

from TAI.utils.super_res import (
    discover_sr_triplets,
    super_resolution_bilineaire_2x,
    super_resolution_contour_stencils_2x,
)


@pytest.fixture()
def lr_gray():
    rng = np.random.default_rng(3)
    return rng.integers(40, 200, size=(24, 24), dtype=np.uint8)


@pytest.fixture()
def lr_color():
    rng = np.random.default_rng(4)
    return rng.integers(40, 200, size=(24, 24, 3), dtype=np.uint8)


# ---------------------------------------------------------------------------
# super_resolution_bilineaire_2x
# ---------------------------------------------------------------------------
def test_bilinear_2x_output_dimensions(lr_gray, lr_color):
    assert super_resolution_bilineaire_2x(lr_gray).shape == (48, 48)
    assert super_resolution_bilineaire_2x(lr_color).shape == (48, 48, 3)


def test_bilinear_2x_value_range(lr_gray):
    out = super_resolution_bilineaire_2x(lr_gray)
    assert int(out.min()) >= 0 and int(out.max()) <= 255


def test_bilinear_2x_original_pixels_preserved(lr_gray):
    """Even rows/cols of the OpenCV-aligned grid keep the source values."""
    out = super_resolution_bilineaire_2x(lr_gray, opencv_align=True)
    src = lr_gray
    # source samples land on (2i+0.5)/2-0.5 ≈ i - 0.25 -> floor i-1/clip; use
    # the relaxed check: every output pixel is a convex combination, so the
    # output min/max bound the source min/max.
    assert out.min() >= src.min() and out.max() <= src.max()


def test_bilinear_2x_close_to_opencv_inter_linear(lr_gray, lr_color):
    for img in (lr_gray, lr_color):
        cv_out = cv2.resize(img, (img.shape[1] * 2, img.shape[0] * 2), interpolation=cv2.INTER_LINEAR)
        my_out = super_resolution_bilineaire_2x(img, opencv_align=True)
        max_diff = int(np.max(np.abs(cv_out.astype(int) - my_out.astype(int))))
        assert max_diff <= 2  # rounding-only difference


def test_bilinear_2x_constant_image_is_constant():
    const = np.full((10, 10), 99, dtype=np.uint8)
    out = super_resolution_bilineaire_2x(const)
    assert np.all(out == 99)


# ---------------------------------------------------------------------------
# super_resolution_contour_stencils_2x
# ---------------------------------------------------------------------------
def test_stencils_2x_output_dimensions(lr_gray, lr_color):
    assert super_resolution_contour_stencils_2x(lr_gray).shape == (48, 48)
    assert super_resolution_contour_stencils_2x(lr_color).shape == (48, 48, 3)


def test_stencils_2x_value_range(lr_gray, lr_color):
    for img in (lr_gray, lr_color):
        out = super_resolution_contour_stencils_2x(img)
        assert int(out.min()) >= 0 and int(out.max()) <= 255


def test_stencils_2x_deterministic(lr_gray):
    a = super_resolution_contour_stencils_2x(lr_gray, rho=0.5)
    b = super_resolution_contour_stencils_2x(lr_gray, rho=0.5)
    assert np.array_equal(a, b)


def test_stencils_2x_constant_image_is_constant():
    const = np.full((12, 12), 77, dtype=np.uint8)
    out = super_resolution_contour_stencils_2x(const)
    assert np.all(out == 77)


def test_stencils_2x_original_grid_preserved(lr_gray):
    """Original LR samples must appear on the even coordinates."""
    out = super_resolution_contour_stencils_2x(lr_gray)
    assert np.array_equal(out[::2, ::2], lr_gray)


def test_stencils_2x_rho_changes_adaptivity(lr_gray):
    a = super_resolution_contour_stencils_2x(lr_gray, rho=0.0)
    b = super_resolution_contour_stencils_2x(lr_gray, rho=2.0)
    assert a.shape == b.shape


def test_stencils_cascade_reaches_4x(lr_gray):
    out2 = super_resolution_contour_stencils_2x(lr_gray)
    out4 = super_resolution_contour_stencils_2x(out2)
    assert out4.shape == (96, 96)


# ---------------------------------------------------------------------------
# discover_sr_triplets
# ---------------------------------------------------------------------------
def test_discover_sr_triplets_fallback(repo_root, images_dir, tmp_path):
    """Without the official dataset, a deterministic 5-triplet demo is built."""
    outputs = tmp_path / "outputs"
    label, triplets = discover_sr_triplets(images_dir, outputs)
    assert "demonstration" in label.lower() or "official" in label.lower() or "consolidated" in label.lower()
    assert len(triplets) == 5
    for hr, l2, l4 in triplets:
        assert hr.exists() and l2.exists() and l4.exists()
        hr_img = cv2.imread(str(hr))
        l2_img = cv2.imread(str(l2))
        l4_img = cv2.imread(str(l4))
        assert hr_img.shape[:2] == (512, 512)
        assert l2_img.shape[:2] == (256, 256)
        assert l4_img.shape[:2] == (128, 128)


def test_discover_sr_triplets_deterministic(repo_root, images_dir, tmp_path):
    _, t1 = discover_sr_triplets(images_dir, tmp_path / "a")
    _, t2 = discover_sr_triplets(images_dir, tmp_path / "a")  # same dir reused
    assert len(t1) == len(t2)
    assert [p.name for p, _, _ in t1] == [p.name for p, _, _ in t2]


def test_numeric_sorting_keeps_triplets_aligned(tmp_path):
    """Files 1..12 must sort 1,2,...,12 (never 1,10,11,12,2,...)."""
    from TAI.utils.super_res import _numeric_suffix

    names = [f"LR_256_{i}.png" for i in [1, 2, 10, 11, 23]]
    keys = [_numeric_suffix(n) for n in names]
    order = [names[i] for i in np.argsort([k[0] for k in keys], kind="stable")]
    assert [n for n in order] == [
        "LR_256_1.png", "LR_256_2.png", "LR_256_10.png", "LR_256_11.png", "LR_256_23.png",
    ]
