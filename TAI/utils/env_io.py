"""Portable environment, path-resolution and I/O helpers for every TAI notebook.

This module removes the ~45-line ``find_project_root`` / ``load_image`` /
``show_images`` boilerplate that used to be copy-pasted into every TAI lab.

Guarantees
----------
* Works identically in local IDEs / Jupyter (VS Code, PyCharm, JupyterLab,
  Jupyter Notebook, CLI ``nbconvert``) regardless of the working directory.
* Works on Google Colab — both after cloning the repository and when a single
  notebook is opened directly from GitHub (the repository is cloned to
  ``/content/APSD_TAI_LAB`` on demand).
* Never uses blocking GUI calls (no ``cv2.imshow``) — everything renders
  through inline Matplotlib.
"""

from __future__ import annotations

import math
import os
import subprocess
import sys
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np

REPO_URL = "https://github.com/Vtheonly/APSD_TAI_LAB.git"
REPO_DIRNAME = "APSD_TAI_LAB"


# ---------------------------------------------------------------------------
# Environment detection & repository discovery
# ---------------------------------------------------------------------------
def in_colab() -> bool:
    """Return True when running inside Google Colab."""
    return "google.colab" in sys.modules or "COLAB_RELEASE_TAG" in os.environ


def find_repo_root(start: str | Path | None = None) -> Path:
    """Walk upward from ``start`` (default: CWD) to the repository root.

    The root is identified by its marker trio: ``README.md`` + ``APDS/`` +
    ``TAI/``. Works from the root itself, from ``TAI/<lab>/notebooks/`` or
    from any nested sub-directory.
    """
    start = Path(start if start is not None else Path.cwd()).resolve()
    for candidate in (start, *start.parents):
        if (
            (candidate / "README.md").is_file()
            and (candidate / "APDS").is_dir()
            and (candidate / "TAI").is_dir()
        ):
            return candidate
    raise FileNotFoundError(
        "Could not locate the APSD_TAI_LAB repository root "
        f"(looked upward from {start}). Launch Jupyter from inside the "
        "repository, or let the Step-0 bootstrap cell clone it on Colab."
    )


def ensure_repo_on_colab() -> Path:
    """Return the repository root inside Google Colab, cloning if necessary.

    Looks first under ``/content`` (fresh runtime or a manual clone), then
    under a mounted Google Drive (``/content/drive/MyDrive``).
    """
    candidates = [
        Path("/content") / REPO_DIRNAME,
        Path("/content/drive/MyDrive") / REPO_DIRNAME,
    ]
    for candidate in candidates:
        if (candidate / "TAI" / "utils").is_dir():
            return candidate.resolve()
    target = Path("/content") / REPO_DIRNAME
    print(f"Cloning {REPO_URL} into {target} ...")
    subprocess.run(
        ["git", "clone", "--depth", "1", REPO_URL, str(target)],
        check=True,
    )
    return target


# ---------------------------------------------------------------------------
# One-call notebook bootstrap
# ---------------------------------------------------------------------------
def bootstrap() -> tuple[Path, Path, Path]:
    """Resolve (and prepare) the TAI workspace.

    Returns ``(repo_root, images_dir, outputs_dir)`` where

    * ``repo_root``   — the APSD_TAI_LAB repository root (cloned on Colab),
    * ``images_dir``  — ``<root>/TAI/images`` (the single deduplicated dataset),
    * ``outputs_dir`` — ``<root>/TAI/outputs`` (created if missing; runtime
      generated images live here and are never committed).

    The repository root is inserted into ``sys.path`` so that
    ``from TAI.utils import ...`` keeps working from any cell afterwards.
    """
    root = ensure_repo_on_colab() if in_colab() else find_repo_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    images_dir = root / "TAI" / "images"
    outputs_dir = root / "TAI" / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    if not images_dir.is_dir():
        raise FileNotFoundError(
            f"TAI image dataset not found at {images_dir}. "
            "Re-clone the repository or restore TAI/images/."
        )
    return root, images_dir, outputs_dir


# ---------------------------------------------------------------------------
# Image I/O
# ---------------------------------------------------------------------------
def default_images_dir() -> Path:
    """Return ``<repo>/TAI/images`` resolved independently of the CWD."""
    root = ensure_repo_on_colab() if in_colab() else find_repo_root()
    return root / "TAI" / "images"


def load_image(
    filename: str,
    flags: int = cv2.IMREAD_COLOR,
    images_dir: str | Path | None = None,
) -> np.ndarray:
    """Load an image from ``TAI/images`` with a CWD-independent absolute path.

    Parameters
    ----------
    filename   : file name inside the consolidated ``TAI/images`` dataset.
    flags      : OpenCV read flags (``cv2.IMREAD_COLOR`` by default).
    images_dir : optional override (defaults to ``TAI/images``).
    """
    base = Path(images_dir) if images_dir is not None else default_images_dir()
    path = base / filename
    img = cv2.imread(str(path), flags)
    if img is None:
        raise FileNotFoundError(f"Image not found or unreadable: {path}")
    return img


# ---------------------------------------------------------------------------
# Inline Matplotlib visualisation helpers (never cv2.imshow!)
# ---------------------------------------------------------------------------
def show_images(
    items,
    cols: int = 3,
    figsize_per_cell: tuple[float, float] = (4.6, 4.0),
    cmap: str = "gray",
) -> None:
    """Display a list of ``(title, image)`` pairs in a Matplotlib grid.

    Grayscale images are rendered with ``vmin=0, vmax=255``; BGR/A images are
    converted to RGB/RGBA on the fly.
    """
    n = len(items)
    rows = math.ceil(n / cols)
    fig, axes = plt.subplots(
        rows, cols, figsize=(cols * figsize_per_cell[0], rows * figsize_per_cell[1])
    )
    axes = np.atleast_1d(axes).ravel()
    for ax in axes[n:]:
        ax.axis("off")
    for ax, (title, img) in zip(axes, items):
        if img.ndim == 2:
            ax.imshow(img, cmap=cmap, vmin=0, vmax=255)
        elif img.shape[2] == 3:
            ax.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        elif img.shape[2] == 4:
            ax.imshow(cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA))
        ax.set_title(title, fontsize=10)
        ax.axis("off")
    plt.tight_layout()
    plt.show()


def plot_image_with_hist(img_list, title_prefix: str = "") -> None:
    """Show images (top row) with their intensity histograms (bottom row).

    Grayscale images produce a single black histogram; colour images produce
    one histogram per B/G/R channel.
    """
    n = len(img_list)
    fig, axes = plt.subplots(2, n, figsize=(5 * n, 7))
    if n == 1:
        axes = axes[:, None]
    for idx, (label, im) in enumerate(img_list):
        if im.ndim == 2:
            axes[0, idx].imshow(im, cmap="gray", vmin=0, vmax=255)
            hist = cv2.calcHist([im], [0], None, [256], [0, 256]).ravel()
            axes[1, idx].plot(hist, color="black")
        else:
            axes[0, idx].imshow(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
            for ch, col in enumerate(("blue", "green", "red")):
                hist = cv2.calcHist([im], [ch], None, [256], [0, 256]).ravel()
                axes[1, idx].plot(hist, color=col, alpha=0.85)
        axes[0, idx].set_title(f"{title_prefix}{label}", fontsize=10)
        axes[0, idx].axis("off")
        axes[1, idx].set_xlim([0, 255])
        axes[1, idx].grid(alpha=0.25)
    plt.tight_layout()
    plt.show()
