"""TAI shared utilities package (single source of truth for all TAI labs).

Modules
-------
env_io      : Colab/local detection, repository-root discovery, ``load_image``,
              ``show_images`` and ``plot_image_with_hist`` helpers.
metrics     : Unified ``calculate_psnr`` / ``calculate_ssim`` quality metrics.
noise       : Deterministic ``add_gaussian_noise`` / ``sp_noise`` generators.
basics      : TP1 from-scratch basics (fixed thresholding, histograms).
filters     : TP2 spatial filters (mean / separable / integral / median /
              bilateral / adaptive / Nagao).
morphology  : TP2 from-scratch morphology + Zhang-Suen thinning.
contrast    : TP2 histogram expansion, global/AHE/CLAHE equalization.
super_res   : TP2 bilinear 2x and Contour-Stencil (Getreuer 2009) super-resolution.

Every TAI notebook bootstraps its environment with::

    from TAI.utils.env_io import bootstrap, load_image, show_images
    ROOT_DIR, IMG_DIR, OUT_DIR = bootstrap()

and imports the pedagogical from-scratch algorithms from these modules so the
implementations stay identical across notebooks and are unit-testable with
pytest (see ``tests/`` at the repository root).
"""

from TAI.utils.env_io import (
    bootstrap,
    in_colab,
    find_repo_root,
    ensure_repo_on_colab,
    load_image,
    show_images,
    plot_image_with_hist,
)
from TAI.utils.metrics import calculate_psnr, calculate_ssim
from TAI.utils.noise import add_gaussian_noise, sp_noise

__all__ = [
    "bootstrap",
    "in_colab",
    "find_repo_root",
    "ensure_repo_on_colab",
    "load_image",
    "show_images",
    "plot_image_with_hist",
    "calculate_psnr",
    "calculate_ssim",
    "add_gaussian_noise",
    "sp_noise",
]
