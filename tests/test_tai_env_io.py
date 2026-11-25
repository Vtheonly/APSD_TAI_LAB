"""TAI.utils.env_io — root resolution, bootstrap and load_image tests."""

import os
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

from TAI.utils import env_io
from TAI.utils.env_io import find_repo_root, load_image


def test_find_repo_root_from_repo_root(repo_root, monkeypatch):
    monkeypatch.chdir(repo_root)
    assert find_repo_root() == repo_root.resolve()


def test_find_repo_root_from_nested_notebook_folder(repo_root, monkeypatch):
    deep = repo_root / "TAI" / "03_TP2_Morphology_and_Contrast" / "notebooks"
    monkeypatch.chdir(deep)
    assert find_repo_root() == repo_root.resolve()


def test_find_repo_root_from_apds_project(repo_root, monkeypatch):
    monkeypatch.chdir(repo_root / "APDS" / "01_Hospital_Data_Setup" / "notebooks")
    assert find_repo_root() == repo_root.resolve()


def test_find_repo_root_from_explicit_start(repo_root):
    start = repo_root / "TAI" / "01_TP1_Image_Fundamentals" / "notebooks"
    assert find_repo_root(start=start) == repo_root.resolve()


def test_find_repo_root_from_arbitrary_path_fails_cleanly(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError, match="repository root"):
        find_repo_root()


def test_find_repo_root_never_leaks_home(monkeypatch, tmp_path):
    """A start deep inside a temp tree raises instead of returning garbage."""
    deep = tmp_path / "a" / "b" / "c"
    deep.mkdir(parents=True)
    with pytest.raises(FileNotFoundError):
        find_repo_root(start=deep)


def test_bootstrap_resolves_all_dirs(repo_root, monkeypatch):
    monkeypatch.chdir(repo_root / "TAI" / "02_TP2_Noise_and_Spatial_Filtering" / "notebooks")
    root, images_dir, outputs_dir = env_io.bootstrap()
    assert root == repo_root.resolve()
    assert images_dir == (repo_root / "TAI" / "images").resolve()
    assert outputs_dir == (repo_root / "TAI" / "outputs").resolve()
    assert images_dir.is_dir() and outputs_dir.is_dir()
    assert str(root) in sys.path


def test_in_colab_is_false_locally():
    assert env_io.in_colab() is False


def test_load_image_from_any_cwd(repo_root, images_dir, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)  # completely outside the repository
    img = load_image("tp1_tp2_cameraman_gray.bmp", cv2.IMREAD_GRAYSCALE, images_dir=images_dir)
    assert img.shape == (256, 256)
    assert img.dtype == np.uint8


def test_load_image_default_dir_from_repo_root(repo_root, monkeypatch):
    monkeypatch.chdir(repo_root)
    img = load_image("tp1_tp2_compteur_water_meter.jpg", cv2.IMREAD_GRAYSCALE)
    assert img.ndim == 2
    assert img.size > 0


def test_load_image_missing_file_raises(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError):
        load_image("does_not_exist.bmp", cv2.IMREAD_GRAYSCALE, images_dir=tmp_path)


def test_show_images_runs_without_gui(small_gray):
    """show_images must render inline (Agg backend) without any window."""
    import matplotlib

    matplotlib.use("Agg", force=True)
    from TAI.utils.env_io import show_images

    show_images([("a", small_gray), ("b", small_gray)], cols=2)
