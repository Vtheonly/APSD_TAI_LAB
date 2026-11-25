#!/usr/bin/env python3
"""
setup_tai_workspace.py

Transactional, all-or-nothing organizer and Jupyter Notebook (.ipynb) solution
generator for Module TAI (Lab TP1 & Lab TP2).

Features:
  - Phase 0 (Pre-flight): Read-only discovery, SHA-256 inventory, zip inspection,
    duplicate/conflict resolution planning, and full JSON + Python AST validation
    of every generated notebook before touching the filesystem.
  - Phase 1 (Staging): Builds the complete reorganized directory tree in an
    isolated staging area, consolidates all TP1 & TP2 images into 'tp1_tp2_images/'
    with uniform descriptive names, preserves all original files without data loss,
    writes all 11 complete .ipynb notebooks, and verifies every SHA-256 checksum.
  - Phase 2 (Atomic Swap + Rollback): Backs up original items, swaps staged tree
    into root, runs post-commit verification, and restores the exact original state
    on any failure or interruption.
"""

import argparse
import ast
import hashlib
import json
import logging
import os
import re
import shutil
import sys
import tempfile
import textwrap
import uuid
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("TAI_Setup")


# ---------------------------------------------------------------------------
# Constants & Canonical Mappings
# ---------------------------------------------------------------------------
IMAGE_EXTENSIONS = {".bmp", ".jpg", ".jpeg", ".png", ".pgm", ".ppm", ".tif", ".tiff"}

CONSOLIDATED_IMAGE_DIR = "tp1_tp2_images"
TARGET_TOP_DIRS = {
    CONSOLIDATED_IMAGE_DIR,
    "tp1_labs",
    "tp2_labs",
    "docs",
    "reference_solutions",
    "archives",
    "misc_preserved",
}

# Lowercase filename -> canonical descriptive image filename inside tp1_tp2_images/
IMAGE_NAME_MAP: Dict[str, str] = {
    # TP1 core images
    "boatscolor.bmp": "tp1_exo2_boats_color.bmp",
    "pepper.bmp": "tp1_exo4_exo5_peppers_color.bmp",
    # Shared TP1 & TP2 core images
    "cameraman.bmp": "tp1_tp2_cameraman_gray.bmp",
    "compteur.jpg": "tp1_tp2_compteur_water_meter.jpg",
    # TP2 core images (from root directory or Images/)
    "tai_globules_rouges.jpg": "tp2_exo4_globules_rouges_cells.jpg",
    "globules_rouges.jpg": "tp2_exo4_globules_rouges_cells.jpg",
    "tai_tp2_glaucome.jpg": "tp2_exo5_glaucoma_retinal_fundus.jpg",
    "glaucome-haut-gauche.jpg": "tp2_exo5_glaucoma_retinal_fundus.jpg",
    # Pre-generated lab outputs if already present in workspace
    "cameraman_bruit_gauss_sig0_001.bmp": "tp2_exo1_cameraman_gauss_noise_var100.bmp",
    "cameraman_bruit_sel_poivre_p_10.bmp": "tp2_exo1_cameraman_salt_pepper_p10.bmp",
    "imgb1.jpg": "tp1_exo3_compteur_binary_imgb1.jpg",
    # Standard shared TAI benchmark sample dataset (TP1 & TP2)
    "airplane.bmp": "tp1_tp2_sample_airplane_f16.bmp",
    "baboon.bmp": "tp1_tp2_sample_baboon_mandrill.bmp",
    "barbara.bmp": "tp1_tp2_sample_barbara_portrait.bmp",
    "bateau.jpg": "tp1_tp2_sample_boat_sailboats.jpg",
    "blobs.bmp": "tp1_tp2_sample_binary_blobs.bmp",
    "boats.bmp": "tp1_tp2_sample_boats_harbor_gray.bmp",
    "bone_scint.pgm": "tp1_tp2_sample_medical_bone_scintigraphy.pgm",
    "brain1.pgm": "tp1_tp2_sample_medical_brain_mri_1.pgm",
    "brain2.pgm": "tp1_tp2_sample_medical_brain_mri_2.pgm",
    "brain3.pgm": "tp1_tp2_sample_medical_brain_mri_3.pgm",
    "brickwall.bmp": "tp1_tp2_sample_texture_brickwall.bmp",
    "bridge.bmp": "tp1_tp2_sample_bridge_landscape.bmp",
    "cablecar.bmp": "tp1_tp2_sample_cablecar_mountain.bmp",
    "clown.bmp": "tp1_tp2_sample_clown_portrait.bmp",
    "earth.bmp": "tp1_tp2_sample_earth_globe.bmp",
    "finger.pgm": "tp1_tp2_sample_fingerprint_1.pgm",
    "fingerprint1.pgm": "tp1_tp2_sample_fingerprint_2.pgm",
    "flower.bmp": "tp1_tp2_sample_flower_close_up.bmp",
    "fruits.bmp": "tp1_tp2_sample_fruits_still_life.bmp",
    "girl.bmp": "tp1_tp2_sample_girl_portrait.bmp",
    "goldhill.bmp": "tp1_tp2_sample_goldhill_village.bmp",
    "houses.bmp": "tp1_tp2_sample_houses_street.bmp",
    "kiel.bmp": "tp1_tp2_sample_kiel_aerial.bmp",
    "lenna.bmp": "tp1_tp2_sample_lenna_portrait.bmp",
    "lighthouse.bmp": "tp1_tp2_sample_lighthouse_coast.bmp",
    "monarch.bmp": "tp1_tp2_sample_monarch_butterfly.bmp",
    "pens.bmp": "tp1_tp2_sample_colored_pens.bmp",
    "saturn.bmp": "tp1_tp2_sample_saturn_planet.bmp",
    "soccer.bmp": "tp1_tp2_sample_soccer_match.bmp",
    "textureb.bmp": "tp1_tp2_sample_texture_pattern.bmp",
    "ultrasound.pgm": "tp1_tp2_sample_medical_ultrasound.pgm",
    "yacht.bmp": "tp1_tp2_sample_yacht_sea.bmp",
    "zoneplate.png": "tp1_tp2_sample_zoneplate_test_pattern.png",
}

REQUIRED_CANONICAL_IMAGES = {
    "tp1_exo2_boats_color.bmp",
    "tp1_exo4_exo5_peppers_color.bmp",
    "tp1_tp2_cameraman_gray.bmp",
    "tp1_tp2_compteur_water_meter.jpg",
    "tp2_exo4_globules_rouges_cells.jpg",
    "tp2_exo5_glaucoma_retinal_fundus.jpg",
}

# Lowercase filename -> canonical relative path inside workspace
NON_IMAGE_NAME_MAP: Dict[str, str] = {
    # Assignments
    "tp1_tai version pour étudiants_ex.pdf": "docs/assignments/tp1_enonce_fr.pdf",
    "tp1_tai version pour étudiants_ex (1).pdf": "docs/assignments/tp1_enonce_fr.pdf",
    "tp1_tai version pour étudiants_eng_ex.pdf": "docs/assignments/tp1_assignment_en.pdf",
    "tai_tp2.pdf": "docs/assignments/tp2_enonce_fr.pdf",
    "tai_tp2 (1).pdf": "docs/assignments/tp2_enonce_fr.pdf",
    # Courses & Papers
    "tai_chap1_pt1.pdf": "docs/courses/tai_chap1_part1.pdf",
    "tai_chap1_pt2.pdf": "docs/courses/tai_chap1_part2.pdf",
    "tai_chap2_pt1+2+3.pdf": "docs/courses/tai_chap2_parts1_2_3.pdf",
    "getreuer_2009_contours_pochoirs.pdf": "docs/references/getreuer_2009_contour_stencils.pdf",
    # Reference code / archives
    "tp2_exo1.py": "reference_solutions/tp2_exo1_reference.py",
    "tp2_exo 2.py": "reference_solutions/tp2_exo2_reference.py",
    "tp1_exo2_3_4_5.rar": "reference_solutions/tp1_exo2_3_4_5_reference.rar",
    "images.zip": "archives/images_original.zip",
    "corrigsdesexercicesdetp.zip": "archives/corrigsdesexercicesdetp_original.zip",
}


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------
@dataclass
class PlannedFileOp:
    source_kind: str  # "disk" or "zip_entry"
    source_path: Path
    zip_member: Optional[str]
    original_rel: str
    dest_rel: str
    sha256: str
    size_bytes: int
    status: str  # "canonical", "duplicate_archived", "conflict_renamed", "zip_extracted"


@dataclass
class WorkspacePlan:
    root_dir: Path
    self_script: Optional[Path]
    original_files: List[Path]
    ops: List[PlannedFileOp] = field(default_factory=list)
    notebooks: Dict[str, dict] = field(default_factory=dict)
    readme_text: str = ""
    manifest_dict: dict = field(default_factory=dict)


class TransactionError(RuntimeError):
    """Raised when any validation, staging, or commit invariant fails."""


# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes_stream(stream) -> Tuple[str, int]:
    h = hashlib.sha256()
    total = 0
    while True:
        chunk = stream.read(1024 * 1024)
        if not chunk:
            break
        h.update(chunk)
        total += len(chunk)
    return h.hexdigest(), total


def sanitize_slug(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower()).strip("_")
    return slug or "unnamed"


def map_image_filename(path_or_name: str, rel_hint: str = "") -> str:
    p = Path(path_or_name)
    fname_lower = p.name.lower()
    ext = p.suffix.lower()

    if fname_lower in IMAGE_NAME_MAP:
        return IMAGE_NAME_MAP[fname_lower]

    # Handle TP2 Exo 6 Super-Resolution dataset if present
    hint_lower = rel_hint.lower()
    m_hr = re.match(r"^hr_gt_(\d+)$", p.stem.lower())
    if m_hr or "hr_gt_512x512" in hint_lower:
        idx = int(m_hr.group(1)) if m_hr else None
        suffix = f"{idx:02d}" if idx is not None else sanitize_slug(p.stem)
        return f"tp2_exo6_sr_hr_gt_512x512_{suffix}{ext}"

    m_lr256 = re.match(r"^lr_256_(\d+)$", p.stem.lower())
    if m_lr256 or "lr_256x256" in hint_lower:
        idx = int(m_lr256.group(1)) if m_lr256 else None
        suffix = f"{idx:02d}" if idx is not None else sanitize_slug(p.stem)
        return f"tp2_exo6_sr_lr_256x256_{suffix}{ext}"

    m_lr128 = re.match(r"^lr_128_(\d+)$", p.stem.lower())
    if m_lr128 or "lr_128x128" in hint_lower:
        idx = int(m_lr128.group(1)) if m_lr128 else None
        suffix = f"{idx:02d}" if idx is not None else sanitize_slug(p.stem)
        return f"tp2_exo6_sr_lr_128x128_{suffix}{ext}"

    return f"tp1_tp2_misc_{sanitize_slug(p.stem)}{ext}"


def resolve_root_dir(cli_root: Optional[str]) -> Path:
    if cli_root:
        return Path(cli_root).expanduser().resolve()
    cwd = Path.cwd().resolve()
    if (cwd / "Images").is_dir() or any(cwd.glob("TAI_*.pdf")):
        return cwd
    candidate = (Path.home() / "Downloads" / "TAI").resolve()
    if candidate.is_dir():
        return candidate
    return cwd


# ---------------------------------------------------------------------------
# Jupyter Notebook Builder & Validator
# ---------------------------------------------------------------------------
def md_cell(text: str) -> dict:
    clean = textwrap.dedent(text).strip()
    return {
        "cell_type": "markdown",
        "id": uuid.uuid4().hex[:12],
        "metadata": {},
        "source": clean.splitlines(keepends=True),
    }


def code_cell(code: str) -> dict:
    clean = textwrap.dedent(code).strip()
    return {
        "cell_type": "code",
        "id": uuid.uuid4().hex[:12],
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": clean.splitlines(keepends=True),
    }


def make_notebook(cells: List[dict]) -> dict:
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "mimetype": "text/x-python",
                "file_extension": ".py",
            },
        },
        "cells": cells,
    }


def validate_notebook_dict(nb_rel_path: str, nb: dict) -> None:
    try:
        serialized = json.dumps(nb, ensure_ascii=False, indent=2)
        parsed = json.loads(serialized)
    except Exception as exc:
        raise TransactionError(f"JSON validation failed for {nb_rel_path}: {exc}") from exc

    if parsed.get("nbformat") != 4:
        raise TransactionError(f"Invalid nbformat in {nb_rel_path}")

    for idx, cell in enumerate(parsed.get("cells", [])):
        if cell.get("cell_type") == "code":
            src = "".join(cell.get("source", []))
            try:
                ast.parse(src)
            except SyntaxError as exc:
                raise TransactionError(
                    f"Python syntax error in {nb_rel_path} cell #{idx + 1} line {exc.lineno}: {exc.msg}\n"
                    f"Line text: {exc.text}"
                ) from exc


def common_setup_cell(lab_folder: str) -> dict:
    return code_cell(
        f"""
        from pathlib import Path
        import math
        import time
        import cv2
        import numpy as np
        import matplotlib.pyplot as plt

        def find_project_root():
            cwd = Path.cwd().resolve()
            for candidate in (cwd, cwd.parent, cwd.parent.parent):
                if (candidate / "tp1_tp2_images").is_dir():
                    return candidate
            raise FileNotFoundError(
                "Impossible de trouver le dossier 'tp1_tp2_images'. "
                "Lancez Jupyter depuis la racine TAI ou depuis tp1_labs / tp2_labs."
            )

        ROOT_DIR = find_project_root()
        IMG_DIR = ROOT_DIR / "tp1_tp2_images"
        OUT_DIR = ROOT_DIR / "{lab_folder}" / "outputs"
        OUT_DIR.mkdir(parents=True, exist_ok=True)

        def load_image(filename, flags=cv2.IMREAD_COLOR):
            path = IMG_DIR / filename
            img = cv2.imread(str(path), flags)
            if img is None:
                raise FileNotFoundError(f"Image introuvable ou illisible: {{path}}")
            return img

        def show_images(items, cols=3, figsize_per_cell=(5, 4)):
            n = len(items)
            rows = math.ceil(n / cols)
            fig, axes = plt.subplots(rows, cols, figsize=(cols * figsize_per_cell[0], rows * figsize_per_cell[1]))
            axes = np.atleast_1d(axes).ravel()
            for ax in axes[n:]:
                ax.axis("off")
            for ax, (title, img) in zip(axes, items):
                if img.ndim == 2:
                    ax.imshow(img, cmap="gray", vmin=0, vmax=255)
                elif img.shape[2] == 3:
                    ax.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                elif img.shape[2] == 4:
                    ax.imshow(cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA))
                ax.set_title(title, fontsize=10)
                ax.axis("off")
            plt.tight_layout()
            plt.show()

        print(f"ROOT_DIR : {{ROOT_DIR}}")
        print(f"IMG_DIR  : {{IMG_DIR}} ({{len(list(IMG_DIR.iterdir()))}} images)")
        print(f"OUT_DIR  : {{OUT_DIR}}")
        """
    )


# ---------------------------------------------------------------------------
# Build All 11 Notebooks (TP1 Exo 1..5 & TP2 Exo 1..6)
# ---------------------------------------------------------------------------
def build_all_notebooks() -> Dict[str, dict]:
    notebooks: Dict[str, dict] = {}

    # -----------------------------------------------------------------------
    # TP1 - Exo 1: Environment Setup & Verification
    # -----------------------------------------------------------------------
    notebooks["tp1_labs/TP1_Exo1_Environment_Setup.ipynb"] = make_notebook([
        md_cell(r"""
        # TP 1 — Exercice 1 : Configuration de l'environnement et vérification des bibliothèques

        Ce notebook valide l'installation des packages Python requis (`numpy`, `opencv-python` / `opencv-contrib-python`, `matplotlib`) ainsi que la structure consolidée du dossier d'images `tp1_tp2_images/`.
        """),
        common_setup_cell("tp1_labs"),
        code_cell(r"""
        import sys
        import importlib

        print(f"Python version : {sys.version.split()[0]}")
        for pkg in ("numpy", "cv2", "matplotlib", "scipy", "skimage"):
            try:
                mod = importlib.import_module(pkg)
                ver = getattr(mod, "__version__", "installed")
                print(f"  [OK] {pkg:12s} : {ver}")
            except ImportError:
                status = "OPTIONNEL" if pkg in ("scipy", "skimage") else "MANQUANT"
                print(f"  [{status}] {pkg}")

        has_ximgproc = hasattr(cv2, "ximgproc")
        print(f"  OpenCV contrib (cv2.ximgproc) disponible : {has_ximgproc}")

        images = sorted(p.name for p in IMG_DIR.iterdir() if p.is_file())
        print(f"\nImages disponibles dans tp1_tp2_images ({len(images)}) :")
        for name in images[:15]:
            print("  -", name)
        if len(images) > 15:
            print(f"  ... et {len(images) - 15} autres images.")
        """),
    ])

    # -----------------------------------------------------------------------
    # TP1 - Exo 2: Image Manipulation & Pixel Access
    # -----------------------------------------------------------------------
    notebooks["tp1_labs/TP1_Exo2_Image_Manipulation.ipynb"] = make_notebook([
        md_cell(r"""
        # TP 1 — Exercice 2 : Manipulations d'une image et bibliothèques spécialisées

        **Objectifs :**
        1. Charger `tp1_exo2_boats_color.bmp` en couleurs (BGR) et en niveaux de gris (`cv2.IMREAD_GRAYSCALE` et `cv2.cvtColor`).
        2. Lire la valeur BGR d'un pixel à la position `(100, 150)`.
        3. Afficher les dimensions `(height, width, channels)` de l'image.
        4. Tracer une ligne horizontale rouge (`[0, 0, 255]` en BGR) au centre de l'image.
        """),
        common_setup_cell("tp1_labs"),
        code_cell(r"""
        # Lecture en couleur (BGR) et en niveaux de gris
        img = load_image("tp1_exo2_boats_color.bmp", cv2.IMREAD_COLOR)
        gray_img = load_image("tp1_exo2_boats_color.bmp", cv2.IMREAD_GRAYSCALE)
        gray_img2 = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        show_images([
            ("Image originale (BGR -> RGB)", img),
            ("Chargée en niveaux de gris", gray_img),
            ("Convertie BGR -> GRAY", gray_img2),
        ], cols=3)

        # Lecture des valeurs BGR à la position (y=100, x=150)
        pixel = img[100, 150]
        print(f"Valeurs BGR du pixel à (100, 150) : {pixel}")

        # Dimensions de l'image
        height, width, channels = img.shape
        print(f"Height: {height} pixels, Width: {width} pixels, Channels: {channels}")

        # Modification de la ligne centrale en rouge [B=0, G=0, R=255]
        img_mod = img.copy()
        mid_row = int(height / 2)
        for i in range(0, width):
            img_mod[mid_row, i] = [0, 0, 255]

        show_images([
            ("Image originale", img),
            ("Image modifiée (ligne centrale rouge)", img_mod),
        ], cols=2)
        """),
    ])

    # -----------------------------------------------------------------------
    # TP1 - Exo 3: Fixed Thresholding
    # -----------------------------------------------------------------------
    notebooks["tp1_labs/TP1_Exo3_Fixed_Thresholding.ipynb"] = make_notebook([
        md_cell(r"""
        # TP 1 — Exercice 3 : Seuillage fixe d'une image

        **Énoncé :** Binariser `tp1_tp2_compteur_water_meter.jpg` (`compteur.jpg`) avec le seuil fixe $T = 80$ :
        - Pixels avec niveau de gris $> 80 \rightarrow 255$ (Blanc)
        - Pixels avec niveau de gris $\le 80 \rightarrow 0$ (Noir)

        Comparer l'implémentation OpenCV (`imgb1`) avec notre algorithme personnel (`imgb2`), puis sauvegarder `imgb1`.
        """),
        common_setup_cell("tp1_labs"),
        code_cell(r"""
        img_gray = load_image("tp1_tp2_compteur_water_meter.jpg", cv2.IMREAD_GRAYSCALE)
        SEUIL = 80

        # 1) Binarisation avec OpenCV
        _, imgb1 = cv2.threshold(img_gray, SEUIL, 255, cv2.THRESH_BINARY)

        # 2) Binarisation avec fonction personnelle (boucles explicites + NumPy)
        def seuillage_fixe_perso(image, seuil=80):
            h, w = image.shape
            out = np.zeros((h, w), dtype=np.uint8)
            for y in range(h):
                for x in range(w):
                    if image[y, x] > seuil:
                        out[y, x] = 255
                    else:
                        out[y, x] = 0
            return out

        imgb2 = seuillage_fixe_perso(img_gray, SEUIL)

        # Vérification d'équivalence stricte
        identiques = np.array_equal(imgb1, imgb2)
        print(f"OpenCV et fonction personnelle strictement identiques : {identiques}")

        # Enregistrement de imgb1 dans tp1_labs/outputs/
        out_path = OUT_DIR / "tp1_exo3_compteur_binary_imgb1.jpg"
        cv2.imwrite(str(out_path), imgb1)
        print(f"Image binaire sauvegardée : {out_path}")

        diff_map = np.abs(imgb1.astype(np.int16) - imgb2.astype(np.int16)).astype(np.uint8)
        show_images([
            ("Originale (NG)", img_gray),
            ("Binaire OpenCV (imgb1)", imgb1),
            ("Binaire Perso (imgb2)", imgb2),
            ("Différence |imgb1 - imgb2|", diff_map),
        ], cols=4)
        """),
    ])

    # -----------------------------------------------------------------------
    # TP1 - Exo 4: Geometric & Drawing Manipulations
    # -----------------------------------------------------------------------
    notebooks["tp1_labs/TP1_Exo4_Geometric_And_Draw_Ops.ipynb"] = make_notebook([
        md_cell(r"""
        # TP 1 — Exercice 4 : Manipulations simples sur des images numériques

        Opérations sur `tp1_exo4_exo5_peppers_color.bmp` (`pepper.bmp`) :
        1. Lecture de `im1` et extraction des dimensions `(h, w)`.
        2. Redimensionnement à moitié taille (`im2`).
        3. Découpage (crop) `[30:150, 200:400]` (`im3`).
        4. Dessin d'un rectangle bleu et texte vert `"Mon rectangle"` (`im4`).
        5. Rotation de 90° (`im5`) et flou Gaussien (`im6`).
        """),
        common_setup_cell("tp1_labs"),
        code_cell(r"""
        # 1) Lire l'image im1
        im1 = load_image("tp1_exo4_exo5_peppers_color.bmp", cv2.IMREAD_COLOR)

        # 2) Taille de im1 dans h et w
        h, w = im1.shape[:2]
        print(f"Dimensions de im1 : h = {h}, w = {w}")

        # 3) Redimensionnement en divisant la taille par 2
        im2 = cv2.resize(im1, (w // 2, h // 2), interpolation=cv2.INTER_AREA)

        # 4) Cropper [y_start=30:y_end=150, x_start=200:x_end=400]
        im3 = im1[30:150, 200:400].copy()

        # 5) Copier im1 dans im4, dessiner rectangle bleu et texte vert
        im4 = im1.copy()
        cv2.rectangle(im4, (200, 30), (400, 150), (255, 0, 0), thickness=2)  # Bleu en BGR
        cv2.putText(
            im4,
            "Mon rectangle",
            (200, 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),  # Vert en BGR
            2,
            cv2.LINE_AA,
        )

        # 6) Rotation de 90°
        im5 = cv2.rotate(im1, cv2.ROTATE_90_CLOCKWISE)

        # 7) Flou Gaussien
        im6 = cv2.GaussianBlur(im1, (7, 7), sigmaX=1.5)

        # 8) Affichage de toutes les images créées
        show_images([
            (f"im1 Originale {im1.shape[:2]}", im1),
            (f"im2 Redimensionnée /2 {im2.shape[:2]}", im2),
            (f"im3 Crop {im3.shape[:2]}", im3),
            ("im4 Rectangle + Texte", im4),
            (f"im5 Rotation 90° {im5.shape[:2]}", im5),
            ("im6 Flou Gaussien", im6),
        ], cols=3)
        """),
    ])

    # -----------------------------------------------------------------------
    # TP1 - Exo 5: Histograms (Grayscale & Color)
    # -----------------------------------------------------------------------
    notebooks["tp1_labs/TP1_Exo5_Image_Histograms.ipynb"] = make_notebook([
        md_cell(r"""
        # TP 1 — Exercice 5 : Histogramme d'une image (Niveaux de gris et Couleurs)

        1. Calculer les histogrammes avec `cv2.calcHist()` pour `tp1_tp2_cameraman_gray.bmp` (`im1`) et `tp1_exo4_exo5_peppers_color.bmp` (`im2`).
        2. Afficher les histogrammes avec Matplotlib.
        3. Implémenter l'algorithme personnel `calcul_histogramme_perso()` et vérifier l'égalité exacte avec OpenCV.
        """),
        common_setup_cell("tp1_labs"),
        code_cell(r"""
        # 1) Lecture des images
        im1 = load_image("tp1_tp2_cameraman_gray.bmp", cv2.IMREAD_GRAYSCALE)
        im2 = load_image("tp1_exo4_exo5_peppers_color.bmp", cv2.IMREAD_COLOR)

        # 2) Calcul avec cv2.calcHist()
        hist1 = cv2.calcHist([im1], [0], None, [256], [0, 256]).ravel()
        hist2_B = cv2.calcHist([im2], [0], None, [256], [0, 256]).ravel()
        hist2_G = cv2.calcHist([im2], [1], None, [256], [0, 256]).ravel()
        hist2_R = cv2.calcHist([im2], [2], None, [256], [0, 256]).ravel()

        # 4) Algorithme personnel
        def calcul_histogramme_perso(canal_2d):
            hist = np.zeros(256, dtype=np.float32)
            h, w = canal_2d.shape
            for y in range(h):
                for x in range(w):
                    hist[canal_2d[y, x]] += 1.0
            return hist

        histp1 = calcul_histogramme_perso(im1)
        histp2_B = calcul_histogramme_perso(im2[:, :, 0])
        histp2_G = calcul_histogramme_perso(im2[:, :, 1])
        histp2_R = calcul_histogramme_perso(im2[:, :, 2])

        # Vérification stricte
        print("Correspondance Cameraman NG :", np.array_equal(hist1, histp1))
        print("Correspondance Peppers B    :", np.array_equal(hist2_B, histp2_B))
        print("Correspondance Peppers G    :", np.array_equal(hist2_G, histp2_G))
        print("Correspondance Peppers R    :", np.array_equal(hist2_R, histp2_R))

        # 3) Affichage Matplotlib
        fig, axes = plt.subplots(2, 2, figsize=(13, 8))
        axes[0, 0].imshow(im1, cmap="gray", vmin=0, vmax=255)
        axes[0, 0].set_title("im1 : Cameraman (Niveaux de gris)")
        axes[0, 0].axis("off")

        axes[0, 1].plot(hist1, color="black", label="OpenCV calcHist")
        axes[0, 1].plot(histp1, "--", color="orange", label="Perso")
        axes[0, 1].set_title("Histogramme im1 (NG)")
        axes[0, 1].set_xlim([0, 255])
        axes[0, 1].set_xlabel("Niveau de gris")
        axes[0, 1].set_ylabel("Nombre de pixels")
        axes[0, 1].legend()
        axes[0, 1].grid(alpha=0.3)

        axes[1, 0].imshow(cv2.cvtColor(im2, cv2.COLOR_BGR2RGB))
        axes[1, 0].set_title("im2 : Peppers (Couleur)")
        axes[1, 0].axis("off")

        axes[1, 1].plot(hist2_R, color="red", label="Rouge (R)")
        axes[1, 1].plot(hist2_G, color="green", label="Vert (G)")
        axes[1, 1].plot(hist2_B, color="blue", label="Bleu (B)")
        axes[1, 1].set_title("Histogrammes RGB de im2")
        axes[1, 1].set_xlim([0, 255])
        axes[1, 1].set_xlabel("Intensité")
        axes[1, 1].set_ylabel("Nombre de pixels")
        axes[1, 1].legend()
        axes[1, 1].grid(alpha=0.3)

        plt.tight_layout()
        plt.show()
        """),
    ])

    # -----------------------------------------------------------------------
    # TP2 - Exo 1: Image Noise (Gaussian & Salt-and-Pepper)
    # -----------------------------------------------------------------------
    notebooks["tp2_labs/TP2_Exo1_Image_Noise.ipynb"] = make_notebook([
        md_cell(r"""
        # TP 2 — Exercice 1 : Bruit d'image (Gaussien additif & Impulsionnel Poivre et Sel)

        1. Charger `tp1_tp2_cameraman_gray.bmp` dans `im1`.
        2. Appliquer un bruit blanc Gaussien de moyenne nulle et de variance $\sigma^2 = 100$ ($\sigma = 10$) $\rightarrow$ `im2`, puis étudier la variation de $\sigma^2$.
        3. Implémenter `sp_noise(image, prob)` et appliquer un bruit poivre et sel avec $p = 0.10$ ($10\%$) $\rightarrow$ `im3`, puis étudier la variation de $p$.
        4. Comparer visuellement et quantitativement les deux types de bruits.
        """),
        common_setup_cell("tp2_labs"),
        code_cell(r"""
        # 1) Lecture de l'image originale en niveaux de gris
        im1 = load_image("tp1_tp2_cameraman_gray.bmp", cv2.IMREAD_GRAYSCALE)
        print(f"Dimensions : {im1.shape}, dtype : {im1.dtype}")

        def add_gaussian_noise(image, variance, seed=42):
            cv2.setRNGSeed(seed)
            sigma = math.sqrt(variance)
            noise = np.zeros(image.shape, dtype=np.float32)
            cv2.randn(noise, 0.0, sigma)
            noisy = cv2.add(image.astype(np.float32), noise)
            return np.clip(noisy, 0, 255).astype(np.uint8)

        def sp_noise(image, prob, seed=42):
            rng = np.random.default_rng(seed)
            output = image.copy()
            if image.ndim == 2:
                black, white = 0, 255
            elif image.shape[2] == 3:
                black = np.array([0, 0, 0], dtype=np.uint8)
                white = np.array([255, 255, 255], dtype=np.uint8)
            else:
                black = np.array([0, 0, 0, 255], dtype=np.uint8)
                white = np.array([255, 255, 255, 255], dtype=np.uint8)
            probs = rng.random(output.shape[:2])
            output[probs < (prob / 2.0)] = black
            output[probs > 1.0 - (prob / 2.0)] = white
            return output

        # 2) Bruit Gaussien variance sigma^2 = 100 (sigma = 10)
        im2 = add_gaussian_noise(im1, variance=100.0, seed=42)
        out_gauss = OUT_DIR / "tp2_exo1_cameraman_gauss_var100.bmp"
        cv2.imwrite(str(out_gauss), im2)

        # 3) Bruit Poivre et Sel p = 0.10 (10%)
        im3 = sp_noise(im1, prob=0.10, seed=42)
        out_sp = OUT_DIR / "tp2_exo1_cameraman_salt_pepper_p10.bmp"
        cv2.imwrite(str(out_sp), im3)

        print(f"Sauvegardés :\n  - {out_gauss}\n  - {out_sp}")
        print(f"PSNR(im1, im2 Gauss var=100) : {cv2.PSNR(im1, im2):.2f} dB")
        print(f"PSNR(im1, im3 S&P p=0.10)    : {cv2.PSNR(im1, im3):.2f} dB")

        show_images([
            ("Originale (im1)", im1),
            ("Bruit Gaussien var=100 (im2)", im2),
            ("Bruit Poivre & Sel p=10% (im3)", im3),
        ], cols=3)
        """),
        code_cell(r"""
        # Variation de sigma^2 (bruit Gaussien) et de p (bruit Poivre & Sel)
        variances = [25, 100, 400, 900]
        probs = [0.02, 0.05, 0.10, 0.25]

        gauss_items = [(f"Gauss var={v} (PSNR={cv2.PSNR(im1, g):.1f} dB)", g)
                       for v in variances for g in [add_gaussian_noise(im1, v)]]
        sp_items = [(f"S&P p={p*100:.0f}% (PSNR={cv2.PSNR(im1, s):.1f} dB)", s)
                    for p in probs for s in [sp_noise(im1, p)]]

        show_images(gauss_items, cols=4)
        show_images(sp_items, cols=4)
        """),
        md_cell(r"""
        ### Observations et comparaison des deux types de bruits

        - **Bruit blanc additif Gaussien (`im2`) :** Affecte **tous les pixels** de l'image avec une petite fluctuation aléatoire centrée en 0. À faible variance ($\sigma^2 = 25$), l'image reste très lisible ; plus $\sigma^2$ augmente ($100 \to 400 \to 900$), plus un grain uniforme apparaît dans les zones homogènes et dégrade les détails fins.
        - **Bruit impulsionnel Poivre et Sel (`im3`) :** N'altère qu'une fraction $p$ des pixels en les remplaçant brutalement par des valeurs extrêmes (`0` noir ou `255` blanc), tandis que $(1-p)$ des pixels conservent exactement leur intensité d'origine. Même à $p=10\%$, le PSNR chute plus fortement ($\sim 15\text{ dB}$) que le bruit gaussien $\sigma^2=100$ ($\sim 28\text{ dB}$) en raison de l'amplitude maximale des erreurs quadratiques $(255)^2$.
        """),
    ])

    # -----------------------------------------------------------------------
    # TP2 - Exo 2: Spatial Filtering, PSNR, Benchmark & Devoir Noté (a, b)
    # -----------------------------------------------------------------------
    notebooks["tp2_labs/TP2_Exo2_Spatial_Filtering_And_PSNR.ipynb"] = make_notebook([
        md_cell(r"""
        # TP 2 — Exercice 2 : Filtrage spatial, métrique PSNR et Devoir noté

        1. Chargement de `im1` (originale), `im2` (bruit gaussien), `im3` (bruit impulsionnel).
        2. Filtre moyenneur $3\times 3$ (OpenCV + fonction personnelle `filtreMoyenne`).
        3. Filtre médian $3\times 3$ sur `im3` et `im2` (OpenCV + fonction personnelle `filtreMedian`).
        4. Calcul et validation de la métrique **PSNR / MSE** (`cv2.PSNR` vs `calculate_psnr`).
        5. Benchmark complet sur `im2` et `im3` (Moyenneur, Gaussien, Médian, Bilatéral OpenCV + `filtrebilateral` corrigé) avec PSNR et temps d'exécution.
        6. **Devoir noté (a) :** Accélération d'un filtre moyenneur de grande taille (Séparabilité 1D et Image Intégrale $O(1)$/pixel).
        7. **Devoir noté (b) :** Filtre moyenne adaptative (formule du cours à seuil $t$ + variante robuste aux impulsions + filtre adaptatif MMSE de Lee) et comparaison PSNR.
        """),
        common_setup_cell("tp2_labs"),
        code_cell(r"""
        # 1) Chargement des images (génération déterministe si TP2_Exo1 n'a pas encore été exécuté)
        im1 = load_image("tp1_tp2_cameraman_gray.bmp", cv2.IMREAD_GRAYSCALE)

        gauss_path = OUT_DIR / "tp2_exo1_cameraman_gauss_var100.bmp"
        sp_path = OUT_DIR / "tp2_exo1_cameraman_salt_pepper_p10.bmp"

        if not gauss_path.exists():
            cv2.setRNGSeed(42)
            g_noise = np.zeros(im1.shape, dtype=np.float32)
            cv2.randn(g_noise, 0.0, 10.0)
            im2 = np.clip(im1.astype(np.float32) + g_noise, 0, 255).astype(np.uint8)
            cv2.imwrite(str(gauss_path), im2)
        else:
            im2 = cv2.imread(str(gauss_path), cv2.IMREAD_GRAYSCALE)

        if not sp_path.exists():
            rng = np.random.default_rng(42)
            im3 = im1.copy()
            probs = rng.random(im1.shape)
            im3[probs < 0.05] = 0
            im3[probs > 0.95] = 255
            cv2.imwrite(str(sp_path), im3)
        else:
            im3 = cv2.imread(str(sp_path), cv2.IMREAD_GRAYSCALE)

        print("Images chargées :", im1.shape, im2.shape, im3.shape)
        """),
        code_cell(r"""
        # Fonctions personnelles : PSNR, Moyenneur, Médian, Bilatéral (corrigé)
        def calculate_psnr(original_image, degraded_image):
            orig = original_image.astype(np.float64)
            deg = degraded_image.astype(np.float64)
            mse = np.mean((orig - deg) ** 2)
            if mse == 0:
                return float("inf")
            return 10.0 * math.log10((255.0 ** 2) / mse)

        def filtreMoyenne(image, taille_fenetre):
            if taille_fenetre % 2 == 0:
                raise ValueError("La taille de la fenêtre doit être impaire.")
            r = taille_fenetre // 2
            padded = np.pad(image.astype(np.float64), r, mode="reflect")
            h, w = image.shape
            acc = np.zeros((h, w), dtype=np.float64)
            for dy in range(taille_fenetre):
                for dx in range(taille_fenetre):
                    acc += padded[dy:dy + h, dx:dx + w]
            return np.clip(np.round(acc / (taille_fenetre * taille_fenetre)), 0, 255).astype(np.uint8)

        def filtreMedian(image, taille_fenetre):
            if taille_fenetre % 2 == 0:
                raise ValueError("La taille de la fenêtre doit être impaire.")
            r = taille_fenetre // 2
            padded = np.pad(image, r, mode="edge")
            windows = np.lib.stride_tricks.sliding_window_view(padded, (taille_fenetre, taille_fenetre))
            return np.median(windows, axis=(-2, -1)).astype(np.uint8)

        def filtrebilateral(image, taille_fenetre, sigma_s, sigma_r):
            if taille_fenetre % 2 == 0:
                raise ValueError("La taille de la fenêtre doit être impaire.")
            r = taille_fenetre // 2
            h, w = image.shape
            img_f = image.astype(np.float64)
            padded = np.pad(img_f, r, mode="reflect")
            sum_weights = np.zeros((h, w), dtype=np.float64)
            sum_values = np.zeros((h, w), dtype=np.float64)
            inv_2s2 = -1.0 / (2.0 * sigma_s * sigma_s)
            inv_2r2 = -1.0 / (2.0 * sigma_r * sigma_r)
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    neighbor = padded[r + dy:r + dy + h, r + dx:r + dx + w]
                    spatial_w = math.exp((dy * dy + dx * dx) * inv_2s2)
                    color_diff = neighbor - img_f
                    color_w = np.exp((color_diff * color_diff) * inv_2r2)
                    w_tot = spatial_w * color_w
                    sum_weights += w_tot
                    sum_values += w_tot * neighbor
            return np.clip(np.round(sum_values / np.maximum(sum_weights, 1e-12)), 0, 255).astype(np.uint8)

        # 2) & 3) Application des filtres 3x3 OpenCV vs Perso
        imf2 = cv2.blur(im2, (3, 3))
        imfp2 = filtreMoyenne(im2, 3)

        imf3 = cv2.medianBlur(im3, 3)
        imfm2 = cv2.medianBlur(im2, 3)
        imfmp = filtreMedian(im3, 3)

        # 4) Validation PSNR (OpenCV vs calculate_psnr)
        pairs = [
            ("PSNR(im1, im2 bruit gauss)", im1, im2),
            ("PSNR(im1, imf2 moyenne 3x3 sur im2)", im1, imf2),
            ("PSNR(im1, imfp2 moyenne perso sur im2)", im1, imfp2),
            ("PSNR(im1, im3 bruit S&P)", im1, im3),
            ("PSNR(im1, imf3 median 3x3 sur im3)", im1, imf3),
            ("PSNR(im1, imfmp median perso sur im3)", im1, imfmp),
            ("PSNR(im1, imfm2 median 3x3 sur im2)", im1, imfm2),
        ]
        print(f"{'Comparaison':42s} | {'cv2.PSNR':>10s} | {'Perso':>10s}")
        print("-" * 68)
        for label, ref, test in pairs:
            print(f"{label:42s} | {cv2.PSNR(ref, test):8.3f} dB | {calculate_psnr(ref, test):8.3f} dB")

        show_images([
            ("Originale (im1)", im1),
            ("Bruit Gaussien (im2)", im2),
            ("Moyenneur 3x3 (imf2)", imf2),
            ("Bruit Poivre & Sel (im3)", im3),
            ("Médian 3x3 sur im3 (imf3)", imf3),
            ("Médian 3x3 sur im2 (imfm2)", imfm2),
        ], cols=3)
        """),
        code_cell(r"""
        # 5) Benchmark complet des filtres sur im2 et im3
        filters = [
            ("Moyenneur 3x3", lambda img: cv2.blur(img, (3, 3))),
            ("Moyenneur 5x5", lambda img: cv2.blur(img, (5, 5))),
            ("Moyenneur 7x7", lambda img: cv2.blur(img, (7, 7))),
            ("Gaussien 3x3, sig=2.0", lambda img: cv2.GaussianBlur(img, (3, 3), 2.0)),
            ("Gaussien 3x3, sig=1.5", lambda img: cv2.GaussianBlur(img, (3, 3), 1.5)),
            ("Gaussien 3x3, sig=1.0", lambda img: cv2.GaussianBlur(img, (3, 3), 1.0)),
            ("Gaussien 3x3, sig=0.5", lambda img: cv2.GaussianBlur(img, (3, 3), 0.5)),
            ("Gaussien 5x5, sig=2.0", lambda img: cv2.GaussianBlur(img, (5, 5), 2.0)),
            ("Gaussien 5x5, sig=1.5", lambda img: cv2.GaussianBlur(img, (5, 5), 1.5)),
            ("Gaussien 5x5, sig=1.0", lambda img: cv2.GaussianBlur(img, (5, 5), 1.0)),
            ("Gaussien 5x5, sig=0.5", lambda img: cv2.GaussianBlur(img, (5, 5), 0.5)),
            ("Médian 3x3", lambda img: cv2.medianBlur(img, 3)),
            ("Médian 5x5", lambda img: cv2.medianBlur(img, 5)),
            ("Médian 7x7", lambda img: cv2.medianBlur(img, 7)),
            ("Bilatéral OpenCV (d=7,40,40)", lambda img: cv2.bilateralFilter(img, 7, 40, 40)),
            ("Bilatéral Perso (7, 2.0, 40)", lambda img: filtrebilateral(img, 7, 2.0, 40.0)),
        ]

        print(f"Baseline -> im2 (Gauss): {calculate_psnr(im1, im2):.2f} dB | im3 (S&P): {calculate_psnr(im1, im3):.2f} dB\n")
        print(f"{'Filtre':30s} | {'PSNR im2 (dB)':>13s} | {'Temps im2 (ms)':>14s} | {'PSNR im3 (dB)':>13s} | {'Temps im3 (ms)':>14s}")
        print("-" * 96)

        best_im2 = (-1.0, "")
        best_im3 = (-1.0, "")
        for name, fn in filters:
            t0 = time.perf_counter()
            out2 = fn(im2)
            dt2 = (time.perf_counter() - t0) * 1000.0
            p2 = calculate_psnr(im1, out2)

            t0 = time.perf_counter()
            out3 = fn(im3)
            dt3 = (time.perf_counter() - t0) * 1000.0
            p3 = calculate_psnr(im1, out3)

            if p2 > best_im2[0]:
                best_im2 = (p2, name)
            if p3 > best_im3[0]:
                best_im3 = (p3, name)
            print(f"{name:30s} | {p2:13.3f} | {dt2:14.3f} | {p3:13.3f} | {dt3:14.3f}")

        print(f"\nMeilleur sur im2 (Gaussien)    : {best_im2[1]} ({best_im2[0]:.3f} dB)")
        print(f"Meilleur sur im3 (Poivre & Sel): {best_im3[1]} ({best_im3[0]:.3f} dB)")
        """),
        md_cell(r"""
        ### Devoir noté (a) : Accélération d'un filtre moyenneur de grande taille

        Pour un masque de taille $k \times k$ sur une image $H \times W$ :
        1. **Approche naïve :** $O(H \cdot W \cdot k^2)$ opérations.
        2. **Approche séparable (1D horizontal puis 1D vertical) :** $O(H \cdot W \cdot 2k)$ opérations (propriété de séparabilité du cours).
        3. **Approche par Image Intégrale (Summed-Area Table) :** $O(H \cdot W)$ indépendant de la taille $k$ (seulement 4 lectures par pixel quelle que soit la taille du filtre !).
        """),
        code_cell(r"""
        def filtreMoyenne_naif_boucles(image, k):
            r = k // 2
            h, w = image.shape
            padded = np.pad(image.astype(np.float64), r, mode="reflect")
            out = np.zeros((h, w), dtype=np.uint8)
            area = float(k * k)
            for i in range(h):
                for j in range(w):
                    out[i, j] = int(round(np.sum(padded[i:i + k, j:j + k]) / area))
            return out

        def filtreMoyenne_separable(image, k):
            r = k // 2
            h, w = image.shape
            padded = np.pad(image.astype(np.float64), r, mode="reflect")
            # Passe horizontale 1D
            horiz = np.zeros((h + 2 * r, w), dtype=np.float64)
            for dx in range(k):
                horiz += padded[:, dx:dx + w]
            horiz /= k
            # Passe verticale 1D
            vert = np.zeros((h, w), dtype=np.float64)
            for dy in range(k):
                vert += horiz[dy:dy + h, :]
            vert /= k
            return np.clip(np.round(vert), 0, 255).astype(np.uint8)

        def filtreMoyenne_integrale(image, k):
            r = k // 2
            h, w = image.shape
            padded = np.pad(image.astype(np.float64), r, mode="reflect")
            sat = np.zeros((padded.shape[0] + 1, padded.shape[1] + 1), dtype=np.float64)
            sat[1:, 1:] = np.cumsum(np.cumsum(padded, axis=0), axis=1)
            sums = sat[k:, k:] - sat[:-k, k:] - sat[k:, :-k] + sat[:-k, :-k]
            return np.clip(np.round(sums / (k * k)), 0, 255).astype(np.uint8)

        print(f"{'Taille':>8s} | {'Naïf (ms)':>11s} | {'Séparable (ms)':>15s} | {'Intégrale O(1) (ms)':>19s} | {'Accélération':>13s} | {'Max diff':>8s}")
        print("-" * 88)
        for k in (7, 15, 25, 35):
            # Naïf mesuré sur 7 et 15 (extrapolé ou mesuré directement car 256x256 reste rapide)
            t0 = time.perf_counter()
            ref = filtreMoyenne_naif_boucles(im2, k)
            dt_naif = (time.perf_counter() - t0) * 1000.0

            t0 = time.perf_counter()
            res_sep = filtreMoyenne_separable(im2, k)
            dt_sep = (time.perf_counter() - t0) * 1000.0

            t0 = time.perf_counter()
            res_int = filtreMoyenne_integrale(im2, k)
            dt_int = (time.perf_counter() - t0) * 1000.0

            max_diff = int(np.max(np.abs(ref.astype(np.int16) - res_int.astype(np.int16))))
            speedup = dt_naif / max(dt_int, 1e-6)
            print(f"{f'{k}x{k}':>8s} | {dt_naif:11.2f} | {dt_sep:15.3f} | {dt_int:19.3f} | {speedup:11.1f}x | {max_diff:8d}")
        """),
        md_cell(r"""
        ### Devoir noté (b) : Filtre moyenne adaptative et comparaison PSNR

        1. **Formule du cours (Slide 42) :**
           $$C[i, j] = \frac{\sum_{k=1}^{L} w(|a_k - A[i,j]|)\, a_k}{\sum_{k=1}^{L} w(|a_k - A[i,j]|)}, \qquad w(x) = \begin{cases} 1 & \text{si } |x| \le t \\ 0 & \text{sinon} \end{cases}$$
        2. **Variante robuste aux impulsions :** si seul le pixel central vérifie $|a_k - A[i,j]| \le t$ (cas typique d'un pixel poivre/sel isolé), on remplace par la médiane locale du voisinage.
        3. **Filtre adaptatif MMSE local (Lee) pour bruit gaussien :** adapte le poids du lissage au rapport entre la variance du bruit $\sigma_n^2$ et la variance locale $\sigma_L^2$.
        """),
        code_cell(r"""
        def filtreMoyenneAdaptative_cours(image, k=5, seuil=30.0, robust_impulsion=False):
            r = k // 2
            h, w = image.shape
            center = image.astype(np.float64)
            padded = np.pad(center, r, mode="reflect")
            windows = np.lib.stride_tricks.sliding_window_view(padded, (k, k))
            diffs = np.abs(windows - center[:, :, None, None])
            weights = (diffs <= seuil).astype(np.float64)
            sum_w = np.sum(weights, axis=(-2, -1))
            sum_val = np.sum(weights * windows, axis=(-2, -1))
            out = sum_val / np.maximum(sum_w, 1.0)
            if robust_impulsion:
                # Si le pixel central est isolé (<= 2 voisins similaires dans la fenêtre), on prend la médiane locale
                isolated = sum_w <= 2.0
                if np.any(isolated):
                    med = np.median(windows, axis=(-2, -1))
                    out = np.where(isolated, med, out)
            return np.clip(np.round(out), 0, 255).astype(np.uint8)

        def filtreMoyenneAdaptative_MMSE(image, k=5, noise_var=100.0):
            r = k // 2
            img_f = image.astype(np.float64)
            padded = np.pad(img_f, r, mode="reflect")
            windows = np.lib.stride_tricks.sliding_window_view(padded, (k, k))
            local_mean = np.mean(windows, axis=(-2, -1))
            local_var = np.var(windows, axis=(-2, -1))
            gain = np.clip(noise_var / np.maximum(local_var, noise_var), 0.0, 1.0)
            out = img_f - gain * (img_f - local_mean)
            return np.clip(np.round(out), 0, 255).astype(np.uint8)

        comp_rows = [
            ("Bruité (référence)", im2, im3),
            ("Moyenneur 3x3", cv2.blur(im2, (3, 3)), cv2.blur(im3, (3, 3))),
            ("Gaussien 3x3 sig=1.0", cv2.GaussianBlur(im2, (3, 3), 1.0), cv2.GaussianBlur(im3, (3, 3), 1.0)),
            ("Médian 3x3", cv2.medianBlur(im2, 3), cv2.medianBlur(im3, 3)),
            ("Bilatéral (d=7,40,40)", cv2.bilateralFilter(im2, 7, 40, 40), cv2.bilateralFilter(im3, 7, 40, 40)),
            ("Moyenne Adaptative Cours (5x5, t=30)", filtreMoyenneAdaptative_cours(im2, 5, 30, False),
             filtreMoyenneAdaptative_cours(im3, 5, 30, False)),
            ("Moyenne Adaptative Robuste (5x5, t=30)", filtreMoyenneAdaptative_cours(im2, 5, 30, True),
             filtreMoyenneAdaptative_cours(im3, 5, 30, True)),
            ("Moyenne Adaptative MMSE Lee (5x5)", filtreMoyenneAdaptative_MMSE(im2, 5, 100.0),
             filtreMoyenneAdaptative_MMSE(im3, 5, 100.0)),
        ]

        print(f"{'Méthode':40s} | {'PSNR im2 (Gauss)':>16s} | {'PSNR im3 (S&P)':>14s}")
        print("-" * 76)
        for label, r2, r3 in comp_rows:
            print(f"{label:40s} | {calculate_psnr(im1, r2):14.3f} dB | {calculate_psnr(im1, r3):12.3f} dB")

        show_images([
            ("Adaptative Cours im2", comp_rows[5][1]),
            ("Adaptative MMSE im2", comp_rows[7][1]),
            ("Adaptative Cours im3", comp_rows[5][2]),
            ("Adaptative Robuste im3", comp_rows[6][2]),
        ], cols=4)
        """),
    ])

    # -----------------------------------------------------------------------
    # TP2 - Exo 3: Nagao Filter
    # -----------------------------------------------------------------------
    notebooks["tp2_labs/TP2_Exo3_Nagao_Filter.ipynb"] = make_notebook([
        md_cell(r"""
        # TP 2 — Exercice 3 : Filtre adaptatif de Nagao

        Le filtre de Nagao découpe une fenêtre centrée autour de chaque pixel en **9 sous-régions** (1 carré central + 4 régions cardinales + 4 régions diagonales). Il remplace le pixel central par la **moyenne de la sous-région présentant la plus faible variance**, préservant ainsi les contours nets tout en lissant les zones homogènes.

        On teste `filtreNagao(im, taille)` pour $5\times 5$, $7\times 7$ et $9\times 9$ sur `im2` (bruit gaussien) et `im3` (bruit impulsionnel).
        """),
        common_setup_cell("tp2_labs"),
        code_cell(r"""
        im1 = load_image("tp1_tp2_cameraman_gray.bmp", cv2.IMREAD_GRAYSCALE)
        gauss_path = OUT_DIR / "tp2_exo1_cameraman_gauss_var100.bmp"
        sp_path = OUT_DIR / "tp2_exo1_cameraman_salt_pepper_p10.bmp"

        if not gauss_path.exists():
            cv2.setRNGSeed(42)
            g_noise = np.zeros(im1.shape, dtype=np.float32)
            cv2.randn(g_noise, 0.0, 10.0)
            im2 = np.clip(im1.astype(np.float32) + g_noise, 0, 255).astype(np.uint8)
        else:
            im2 = cv2.imread(str(gauss_path), cv2.IMREAD_GRAYSCALE)

        if not sp_path.exists():
            rng = np.random.default_rng(42)
            im3 = im1.copy()
            probs = rng.random(im1.shape)
            im3[probs < 0.05] = 0
            im3[probs > 0.95] = 255
        else:
            im3 = cv2.imread(str(sp_path), cv2.IMREAD_GRAYSCALE)

        def calculate_psnr(a, b):
            mse = np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2)
            return float("inf") if mse == 0 else 10.0 * math.log10((255.0 ** 2) / mse)

        def build_nagao_masks(taille_filtre):
            if taille_filtre < 5 or taille_filtre % 2 == 0:
                raise ValueError("La taille du filtre Nagao doit être impaire et >= 5.")
            r = taille_filtre // 2
            c = r  # index du centre dans la matrice k x k
            masks = []

            # 1) Masque central (3x3 pour 5x5 et 7x7, 5x5 pour 9x9)
            kc = 1 if r <= 3 else r // 2
            m_center = np.zeros((taille_filtre, taille_filtre), dtype=np.float64)
            m_center[c - kc:c + kc + 1, c - kc:c + kc + 1] = 1.0
            masks.append(m_center)

            # 2) Masque Nord (et rotations 90°, 180°, 270° pour Ouest, Sud, Est)
            m_north = np.zeros((taille_filtre, taille_filtre), dtype=np.float64)
            m_north[c, c] = 1.0
            for dr in range(1, r + 1):
                half_w = min(dr, max(1, r - 1))
                m_north[c - dr, c - half_w:c + half_w + 1] = 1.0
            for rot in range(4):
                masks.append(np.rot90(m_north, k=rot))

            # 3) Masque Nord-Ouest (et rotations 90°, 180°, 270° pour SW, SE, NE)
            m_nw = np.zeros((taille_filtre, taille_filtre), dtype=np.float64)
            m_nw[c, c] = 1.0
            m_nw[c - 1, c] = 1.0
            m_nw[c, c - 1] = 1.0
            m_nw[0:c, 0:c] = 1.0
            for rot in range(4):
                masks.append(np.rot90(m_nw, k=rot))

            return masks

        def filtreNagao(im, taille_filtre=5, iterations=1):
            masks = build_nagao_masks(taille_filtre)
            current = im.astype(np.float64)
            for _ in range(iterations):
                img_sq = current * current
                means = []
                variances = []
                for mask in masks:
                    kernel = mask / np.sum(mask)
                    mean = cv2.filter2D(current, cv2.CV_64F, kernel, borderType=cv2.BORDER_REFLECT)
                    mean_sq = cv2.filter2D(img_sq, cv2.CV_64F, kernel, borderType=cv2.BORDER_REFLECT)
                    var = np.maximum(0.0, mean_sq - mean * mean)
                    means.append(mean)
                    variances.append(var)
                means_stack = np.stack(means, axis=0)
                vars_stack = np.stack(variances, axis=0)
                best_idx = np.argmin(vars_stack, axis=0)
                current = np.take_along_axis(means_stack, best_idx[None, :, :], axis=0)[0]
            return np.clip(np.round(current), 0, 255).astype(np.uint8)

        # Vérification des 9 sous-masques 5x5
        masks5 = build_nagao_masks(5)
        print("Nombre de sous-régions :", len(masks5), "| Tailles :", [int(m.sum()) for m in masks5])

        sizes = [5, 7, 9]
        results_im2 = []
        results_im3 = []
        print(f"\nBaseline -> im2: {calculate_psnr(im1, im2):.3f} dB | im3: {calculate_psnr(im1, im3):.3f} dB\n")
        print(f"{'Fenêtre Nagao':16s} | {'PSNR im2 (Gauss)':>16s} | {'PSNR im3 (S&P)':>14s}")
        print("-" * 54)
        for sz in sizes:
            out2 = filtreNagao(im2, sz)
            out3 = filtreNagao(im3, sz)
            results_im2.append((f"Nagao {sz}x{sz} (im2, {calculate_psnr(im1, out2):.2f} dB)", out2))
            results_im3.append((f"Nagao {sz}x{sz} (im3, {calculate_psnr(im1, out3):.2f} dB)", out3))
            print(f"{f'{sz}x{sz}':16s} | {calculate_psnr(im1, out2):14.3f} dB | {calculate_psnr(im1, out3):12.3f} dB")

        out2_iter3 = filtreNagao(im2, 5, iterations=3)
        print(f"{'5x5 (3 itér.)':16s} | {calculate_psnr(im1, out2_iter3):14.3f} dB | {'-':>14s}")

        show_images([("Originale", im1)] + results_im2, cols=4)
        show_images([("Bruit S&P", im3)] + results_im3, cols=4)
        """),
        md_cell(r"""
        ### Analyse des résultats du filtre de Nagao

        - **Sur le bruit Gaussien (`im2`) :** Le filtre de Nagao $5\times 5$ améliore nettement le PSNR par rapport à l'image bruitée tout en conservant des contours très nets (effet *cartoon/peinture* qui renforce les transitions). Augmenter la fenêtre vers $7\times 7$ et $9\times 9$ élargit les sous-régions, ce qui tend à gommer certains détails fins et faire baisser légèrement le PSNR.
        - **Sur le bruit Poivre et Sel (`im3`) :** Contrairement au moyenneur classique, Nagao évite automatiquement les cliques contenant un pixel aberrant (car sa variance explose) tant qu'au moins une des 9 cliques autour du pixel est saine. Toutefois, à $p=10\%$ et lorsque le pixel central lui-même est corrompu (0 ou 255), toutes les cliques contiennent le pixel central : le filtre médian reste donc supérieur sur le bruit impulsionnel pur.
        """),
    ])

    # -----------------------------------------------------------------------
    # TP2 - Exo 4: Mathematical Morphology
    # -----------------------------------------------------------------------
    notebooks["tp2_labs/TP2_Exo4_Mathematical_Morphology.ipynb"] = make_notebook([
        md_cell(r"""
        # TP 2 — Exercice 4 : Morphologie mathématique

        Image : `tp2_exo4_globules_rouges_cells.jpg` (`Globules_rouges.jpg`).
        1. Binarisation dans `imb1` et application de l'**érosion**, **dilatation**, **ouverture** et **fermeture** ($3\times 3$, $5\times 5$, $7\times 7$) via OpenCV puis fonctions personnelles.
        2. Séparation et comptage des globules rouges par combinaison morphologique + transformée de distance / Watershed.
        3. Squelettisation morphologique par l'algorithme de **Zhang-Suen** (`cv2.ximgproc.thinning` + implémentation NumPy autonome).
        """),
        common_setup_cell("tp2_labs"),
        code_cell(r"""
        # Lecture en niveaux de gris et binarisation automatique (globules en blanc = 255, fond en noir = 0)
        im1 = load_image("tp2_exo4_globules_rouges_cells.jpg", cv2.IMREAD_GRAYSCALE)
        otsu_t, _ = cv2.threshold(im1, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        border_vals = np.concatenate([im1[0, :], im1[-1, :], im1[:, 0], im1[:, -1]])
        if np.median(border_vals) > otsu_t:
            _, imb1 = cv2.threshold(im1, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        else:
            _, imb1 = cv2.threshold(im1, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        print(f"Seuil d'Otsu retenu : {otsu_t:.1f} | Pixels foreground : {np.mean(imb1 > 0)*100:.1f}%")

        # Fonctions morphologiques personnelles
        def ma_erosion(img, kernel):
            kh, kw = kernel.shape
            rh, rw = kh // 2, kw // 2
            h, w = img.shape
            padded = np.pad(img, ((rh, rh), (rw, rw)), mode="edge")
            out = np.full((h, w), 255, dtype=img.dtype)
            for dy in range(kh):
                for dx in range(kw):
                    if kernel[dy, dx] > 0:
                        out = np.minimum(out, padded[dy:dy + h, dx:dx + w])
            return out

        def ma_dilatation(img, kernel):
            kh, kw = kernel.shape
            rh, rw = kh // 2, kw // 2
            h, w = img.shape
            padded = np.pad(img, ((rh, rh), (rw, rw)), mode="edge")
            out = np.zeros((h, w), dtype=img.dtype)
            for dy in range(kh):
                for dx in range(kw):
                    if kernel[dy, dx] > 0:
                        out = np.maximum(out, padded[dy:dy + h, dx:dx + w])
            return out

        def ma_ouverture(img, kernel):
            return ma_dilatation(ma_erosion(img, kernel), kernel)

        def ma_fermeture(img, kernel):
            return ma_erosion(ma_dilatation(img, kernel), kernel)

        # 1) Test 3x3, 5x5, 7x7 OpenCV vs Perso
        viz_items = [("Originale (NG)", im1), ("Binaire Otsu (imb1)", imb1)]
        for ksize in (3, 5, 7):
            es = np.ones((ksize, ksize), dtype=np.uint8)
            cv_ero = cv2.erode(imb1, es)
            cv_dil = cv2.dilate(imb1, es)
            cv_ouv = cv2.morphologyEx(imb1, cv2.MORPH_OPEN, es)
            cv_fer = cv2.morphologyEx(imb1, cv2.MORPH_CLOSE, es)

            my_ero = ma_erosion(imb1, es)
            my_dil = ma_dilatation(imb1, es)
            my_ouv = ma_ouverture(imb1, es)
            my_fer = ma_fermeture(imb1, es)

            print(
                f"ES {ksize}x{ksize} -> Égalité stricte OpenCV/Perso : "
                f"Ero={np.array_equal(cv_ero, my_ero)}, "
                f"Dil={np.array_equal(cv_dil, my_dil)}, "
                f"Ouv={np.array_equal(cv_ouv, my_ouv)}, "
                f"Fer={np.array_equal(cv_fer, my_fer)}"
            )
            if ksize == 5:
                viz_items.extend([
                    ("Érosion 5x5", my_ero),
                    ("Dilatation 5x5", my_dil),
                    ("Ouverture 5x5", my_ouv),
                    ("Fermeture 5x5", my_fer),
                ])

        show_images(viz_items, cols=3)
        """),
        code_cell(r"""
        # 2) Séparation et comptage des globules rouges
        # Étape A : Fermeture puis remplissage des trous internes + ouverture pour supprimer le bruit
        k_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        closed = cv2.morphologyEx(imb1, cv2.MORPH_CLOSE, k_small, iterations=2)

        # Remplissage de trous via contours externes
        contours_fill, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        filled = np.zeros_like(closed)
        cv2.drawContours(filled, contours_fill, -1, 255, thickness=cv2.FILLED)
        clean = cv2.morphologyEx(filled, cv2.MORPH_OPEN, k_small, iterations=1)

        raw_num, _ = cv2.connectedComponents(clean)

        # Étape B : Transformée en distance + marqueurs + Watershed pour séparer les globules accolés
        dist = cv2.distanceTransform(clean, cv2.DIST_L2, 5)
        dist_smooth = cv2.GaussianBlur(dist, (5, 5), 0)
        sure_bg = cv2.dilate(clean, k_small, iterations=2)
        _, sure_fg = cv2.threshold(dist_smooth, 0.42 * dist_smooth.max(), 255, cv2.THRESH_BINARY)
        sure_fg = sure_fg.astype(np.uint8)
        unknown = cv2.subtract(sure_bg, sure_fg)

        n_markers, markers = cv2.connectedComponents(sure_fg)
        markers = markers + 1
        markers[unknown == 255] = 0
        img_color = cv2.cvtColor(im1, cv2.COLOR_GRAY2BGR)
        markers_ws = cv2.watershed(img_color.copy(), markers)

        # Comptage final et annotation
        cell_count = 0
        annotated = img_color.copy()
        annotated[markers_ws == -1] = [0, 0, 255]  # frontières watershed en rouge
        for label_id in range(2, n_markers + 1):
            mask_cell = (markers_ws == label_id).astype(np.uint8)
            area = int(np.sum(mask_cell))
            if area < 40:
                continue
            cell_count += 1
            ys, xs = np.where(mask_cell > 0)
            cy, cx = int(np.mean(ys)), int(np.mean(xs))
            cv2.putText(annotated, str(cell_count), (cx - 8, cy + 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 200, 0), 1, cv2.LINE_AA)

        print(f"Composantes avant séparation : {raw_num - 1}")
        print(f"Nombre de globules rouges comptés après séparation morphologique : {cell_count}")

        show_images([
            ("Masque nettoyé", clean),
            ("Carte de distance", cv2.normalize(dist, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)),
            ("Marqueurs séparés (sure_fg)", sure_fg),
            (f"Globules séparés & comptés ({cell_count})", annotated),
        ], cols=4)
        """),
        code_cell(r"""
        # 3) Squelettisation de Zhang-Suen
        def zhang_suen_thinning_perso(binary_img):
            img = (binary_img > 0).astype(np.uint8)
            changed = True
            while changed:
                changed = False
                for step in (0, 1):
                    p = np.pad(img, 1, mode="constant", constant_values=0)
                    p2, p3, p4 = p[:-2, 1:-1], p[:-2, 2:], p[1:-1, 2:]
                    p5, p6, p7 = p[2:, 2:], p[2:, 1:-1], p[2:, :-2]
                    p8, p9 = p[1:-1, :-2], p[:-2, :-2]
                    b = p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
                    neighbors = [p2, p3, p4, p5, p6, p7, p8, p9, p2]
                    a = np.zeros_like(img, dtype=np.uint8)
                    for k in range(8):
                        a += ((neighbors[k] == 0) & (neighbors[k + 1] == 1)).astype(np.uint8)
                    if step == 0:
                        c1 = (p2 * p4 * p6) == 0
                        c2 = (p4 * p6 * p8) == 0
                    else:
                        c1 = (p2 * p4 * p8) == 0
                        c2 = (p2 * p6 * p8) == 0
                    cond = (img == 1) & (b >= 2) & (b <= 6) & (a == 1) & c1 & c2
                    if np.any(cond):
                        img[cond] = 0
                        changed = True
            return (img * 255).astype(np.uint8)

        skel_perso = zhang_suen_thinning_perso(clean)
        items_skel = [("Masque binaire nettoyé", clean), ("Squelette Zhang-Suen (Perso)", skel_perso)]

        if hasattr(cv2, "ximgproc"):
            skel_cv = cv2.ximgproc.thinning(clean, thinningType=cv2.ximgproc.THINNING_ZHANGSUEN)
            print("cv2.ximgproc.thinning disponible ! Égalité avec version perso :", np.array_equal(skel_cv, skel_perso))
            items_skel.append(("Squelette OpenCV ximgproc", skel_cv))
        else:
            print("Module cv2.ximgproc absent (opencv-contrib-python non installé) -> fallback perso utilisé.")

        show_images(items_skel, cols=len(items_skel))
        """),
    ])

    # -----------------------------------------------------------------------
    # TP2 - Exo 5: Histogram Expansion, Global Equalization, AHE & CLAHE
    # -----------------------------------------------------------------------
    notebooks["tp2_labs/TP2_Exo5_Histogram_And_Contrast.ipynb"] = make_notebook([
        md_cell(r"""
        # TP 2 — Exercice 5 : Amélioration d'histogramme et de contraste

        Images : `tp1_tp2_compteur_water_meter.jpg` (`im1` en NG) et `tp2_exo5_glaucoma_retinal_fundus.jpg` (`imc1` en couleur).
        1. **Expansion dynamique :** `cv2.normalize()` + fonction personnelle `expansionHisto(image, seuil=0, Ymin=0, Ymax=255)`.
        2. **Égalisation d'histogramme** (sur canal $L$ dans l'espace Lab pour l'image couleur `imc1`) :
           - a) Égalisation globale (`cv2.equalizeHist` + `egalisationHistoGlobale`)
           - b) Égalisation adaptative AHE (OpenCV + `egalisationAHE` avec interpolation bilinéaire entre blocs)
           - c) Égalisation adaptative limitée CLAHE (`cv2.createCLAHE` + `egalisationCLAHE` avec *clip limit* et redistribution uniforme)
        """),
        common_setup_cell("tp2_labs"),
        code_cell(r"""
        im1 = load_image("tp1_tp2_compteur_water_meter.jpg", cv2.IMREAD_GRAYSCALE)
        imc1 = load_image("tp2_exo5_glaucoma_retinal_fundus.jpg", cv2.IMREAD_COLOR)

        def plot_image_with_hist(img_list, title_prefix=""):
            n = len(img_list)
            fig, axes = plt.subplots(2, n, figsize=(5 * n, 7))
            if n == 1:
                axes = axes[:, None]
            for idx, (label, im) in enumerate(img_list):
                if im.ndim == 2:
                    axes[0, idx].imshow(im, cmap="gray", vmin=0, vmax=255)
                    h = cv2.calcHist([im], [0], None, [256], [0, 256]).ravel()
                    axes[1, idx].plot(h, color="black")
                else:
                    axes[0, idx].imshow(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
                    for ch, col in enumerate(("blue", "green", "red")):
                        h = cv2.calcHist([im], [ch], None, [256], [0, 256]).ravel()
                        axes[1, idx].plot(h, color=col, alpha=0.85)
                axes[0, idx].set_title(f"{title_prefix}{label}", fontsize=10)
                axes[0, idx].axis("off")
                axes[1, idx].set_xlim([0, 255])
                axes[1, idx].grid(alpha=0.25)
            plt.tight_layout()
            plt.show()

        # 1.a) Histogrammes originaux
        plot_image_with_hist([("im1 (NG originale)", im1), ("imc1 (Couleur originale)", imc1)])
        """),
        code_cell(r"""
        # 1.b) cv2.normalize() et 1.c) expansionHisto()
        im2_cv = cv2.normalize(im1, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
        imc2_cv = cv2.normalize(imc1, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)

        def expansion_canal(canal, seuil=0, Ymin=0, Ymax=255):
            hist = np.bincount(canal.ravel(), minlength=256)
            valid = np.where(hist > seuil)[0]
            if len(valid) == 0:
                Xmin, Xmax = int(canal.min()), int(canal.max())
            else:
                Xmin, Xmax = int(valid[0]), int(valid[-1])
            if Xmax == Xmin:
                return np.full_like(canal, Ymin, dtype=np.uint8)
            alpha = (Ymin * Xmax - Ymax * Xmin) / (Xmax - Xmin)
            beta = (Ymax - Ymin) / (Xmax - Xmin)
            res = alpha + beta * canal.astype(np.float64)
            return np.clip(np.round(res), Ymin, Ymax).astype(np.uint8)

        def expansionHisto(image, seuil=0, Ymin=0, Ymax=255):
            if image.ndim == 2:
                return expansion_canal(image, seuil, Ymin, Ymax)
            # Étirement par canal (ou sur luminance Lab)
            out = np.empty_like(image)
            for c in range(image.shape[2]):
                out[:, :, c] = expansion_canal(image[:, :, c], seuil, Ymin, Ymax)
            return out

        im2_perso = expansionHisto(im1, seuil=0, Ymin=0, Ymax=255)
        imc2_perso = expansionHisto(imc1, seuil=0, Ymin=0, Ymax=255)
        im2_seuil = expansionHisto(im1, seuil=20, Ymin=0, Ymax=255)

        print("Diff max |cv2.normalize - expansionHisto| (NG)     :", np.max(np.abs(im2_cv.astype(int) - im2_perso.astype(int))))
        print("Diff max |cv2.normalize - expansionHisto| (Couleur):", np.max(np.abs(imc2_cv.astype(int) - imc2_perso.astype(int))))

        plot_image_with_hist([
            ("im1 Originale", im1),
            ("cv2.normalize", im2_cv),
            ("expansionHisto (seuil=0)", im2_perso),
            ("expansionHisto (seuil=20)", im2_seuil),
        ])
        plot_image_with_hist([
            ("imc1 Originale", imc1),
            ("cv2.normalize", imc2_cv),
            ("expansionHisto (seuil=0)", imc2_perso),
        ])
        """),
        code_cell(r"""
        # 2) Égalisation d'histogramme : Globale, AHE et CLAHE (OpenCV + Perso)
        def egalisation_globale_canal(canal):
            hist = np.bincount(canal.ravel(), minlength=256)
            hc = np.cumsum(hist)
            nz = np.where(hc > 0)[0]
            if len(nz) == 0:
                return canal.copy()
            hc_min = hc[nz[0]]
            n_pix = canal.size
            if n_pix == hc_min:
                return canal.copy()
            lut = np.round(255.0 * (hc - hc_min) / (n_pix - hc_min))
            lut = np.clip(lut, 0, 255).astype(np.uint8)
            return lut[canal]

        def egalisation_locale_blocs(canal, tile_grid=(8, 8), clip_limit=None):
            h, w = canal.shape
            ty, tx = tile_grid
            pad_h = (ty - (h % ty)) % ty
            pad_w = (tx - (w % tx)) % tx
            padded = np.pad(canal, ((0, pad_h), (0, pad_w)), mode="reflect")
            ph, pw = padded.shape
            th, tw = ph // ty, pw // tx

            luts = np.zeros((ty, tx, 256), dtype=np.float64)
            n_tile = th * tw
            for iy in range(ty):
                for ix in range(tx):
                    tile = padded[iy * th:(iy + 1) * th, ix * tw:(ix + 1) * tw]
                    hist = np.bincount(tile.ravel(), minlength=256).astype(np.int64)
                    if clip_limit is not None and clip_limit > 0:
                        limit = max(1, int(round(clip_limit * n_tile / 256.0)))
                        excess = np.sum(np.maximum(0, hist - limit))
                        hist = np.minimum(hist, limit)
                        avg_inc = excess // 256
                        rem = int(excess % 256)
                        hist += avg_inc
                        if rem > 0:
                            step = max(1, 256 // rem)
                            indices = np.arange(0, 256, step)[:rem]
                            hist[indices] += 1
                    hc = np.cumsum(hist).astype(np.float64)
                    lut = np.round(255.0 * hc / max(1.0, hc[-1]))
                    luts[iy, ix] = np.clip(lut, 0, 255)

            # Interpolation bilinéaire entre les centres des blocs
            ys = np.arange(h, dtype=np.float64)
            xs = np.arange(w, dtype=np.float64)
            gy = (ys + 0.5) / th - 0.5
            gx = (xs + 0.5) / tw - 0.5
            y0 = np.clip(np.floor(gy).astype(np.int64), 0, ty - 1)
            x0 = np.clip(np.floor(gx).astype(np.int64), 0, tx - 1)
            y1 = np.clip(y0 + 1, 0, ty - 1)
            x1 = np.clip(x0 + 1, 0, tx - 1)
            wy = np.clip(gy - y0, 0.0, 1.0)[:, None]
            wx = np.clip(gx - x0, 0.0, 1.0)[None, :]

            v00 = luts[y0[:, None], x0[None, :], canal]
            v01 = luts[y0[:, None], x1[None, :], canal]
            v10 = luts[y1[:, None], x0[None, :], canal]
            v11 = luts[y1[:, None], x1[None, :], canal]

            out = (
                (1.0 - wy) * (1.0 - wx) * v00
                + (1.0 - wy) * wx * v01
                + wy * (1.0 - wx) * v10
                + wy * wx * v11
            )
            return np.clip(np.round(out), 0, 255).astype(np.uint8)

        def apply_on_gray_or_lab(image, func_2d):
            if image.ndim == 2:
                return func_2d(image)
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2Lab)
            lab[:, :, 0] = func_2d(lab[:, :, 0])
            return cv2.cvtColor(lab, cv2.COLOR_Lab2BGR)

        # Fonctions personnelles
        egalisationHistoGlobale = lambda img: apply_on_gray_or_lab(img, egalisation_globale_canal)
        egalisationAHE = lambda img: apply_on_gray_or_lab(img, lambda c: egalisation_locale_blocs(c, (8, 8), None))
        egalisationCLAHE = lambda img: apply_on_gray_or_lab(img, lambda c: egalisation_locale_blocs(c, (8, 8), 2.0))

        # Fonctions OpenCV
        cv_glob = lambda img: apply_on_gray_or_lab(img, cv2.equalizeHist)
        cv_ahe_obj = cv2.createCLAHE(clipLimit=1000.0, tileGridSize=(8, 8))
        cv_clahe_obj = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cv_ahe = lambda img: apply_on_gray_or_lab(img, cv_ahe_obj.apply)
        cv_clahe = lambda img: apply_on_gray_or_lab(img, cv_clahe_obj.apply)

        plot_image_with_hist([
            ("Globale OpenCV", cv_glob(im1)),
            ("Globale Perso", egalisationHistoGlobale(im1)),
            ("AHE OpenCV", cv_ahe(im1)),
            ("AHE Perso", egalisationAHE(im1)),
            ("CLAHE OpenCV", cv_clahe(im1)),
            ("CLAHE Perso", egalisationCLAHE(im1)),
        ])

        plot_image_with_hist([
            ("imc1 Globale OpenCV", cv_glob(imc1)),
            ("imc1 Globale Perso", egalisationHistoGlobale(imc1)),
            ("imc1 AHE Perso", egalisationAHE(imc1)),
            ("imc1 CLAHE OpenCV", cv_clahe(imc1)),
            ("imc1 CLAHE Perso", egalisationCLAHE(imc1)),
        ])
        """),
    ])

    # -----------------------------------------------------------------------
    # TP2 - Exo 6: Super-Resolution & Getreuer (2009) Contour Stencils
    # -----------------------------------------------------------------------
    notebooks["tp2_labs/TP2_Exo6_Super_Resolution.ipynb"] = make_notebook([
        md_cell(r"""
        # TP 2 — Exercice 6 : Super-résolution des images et Contours Pochoirs (Getreuer, 2009)

        1. Chargement du dataset `Images_TP2_EXO6_SR` (23 images : `HR_GT_512x512`, `LR_256x256`, `LR_128x128`) depuis `tp1_tp2_images/` ou repli automatique sur un jeu de test local généré à partir de `tp1_tp2_images/` si l'archive externe n'a pas encore été téléchargée.
        2. Évaluation PSNR et SSIM des interpolations OpenCV (`INTER_NEAREST`, `INTER_LINEAR`, `INTER_CUBIC`) en $2\times$, $4\times$ direct et double $2\times$ ($2\times \to 2\times$).
        3. Implémentation personnelle de l'interpolation bilinéaire $2\times$ (`super_resolution_bilineaire_2x`) et comparaison avec OpenCV.
        4. Implémentation complète de l'interpolation adaptative par **Contours Pochoirs** (*Contour Stencils*, Getreuer 2009) : calcul de variation totale sur les 12 stencils, norme vectorielle $\ell_1$ en $YC_bC_r$ pour les images couleur, filtrage spatial $G_\rho$, règles d'interpolation par cellule et moyennage des points milieux partagés.
        """),
        common_setup_cell("tp2_labs"),
        code_cell(r"""
        # 1) Découverte du dataset SR (consolidé, sous-dossier ou génération locale de démonstration)
        def discover_sr_dataset():
            # Cas A : images déjà consolidées dans tp1_tp2_images/
            hr_files = sorted(IMG_DIR.glob("tp2_exo6_sr_hr_gt_512x512_*"))
            lr256_files = sorted(IMG_DIR.glob("tp2_exo6_sr_lr_256x256_*"))
            lr128_files = sorted(IMG_DIR.glob("tp2_exo6_sr_lr_128x128_*"))
            if hr_files and len(hr_files) == len(lr256_files) == len(lr128_files):
                return "Dataset consolidé tp1_tp2_images", list(zip(hr_files, lr256_files, lr128_files))

            # Cas B : dossier Images_TP2_EXO6_SR extrait dans tp1_tp2_images/ ou à la racine
            for base in (IMG_DIR / "Images_TP2_EXO6_SR", ROOT_DIR / "Images_TP2_EXO6_SR", ROOT_DIR / "Images" / "Images_TP2_EXO6_SR"):
                hr_dir, lr2_dir, lr4_dir = base / "HR_GT_512x512", base / "LR_256x256", base / "LR_128x128"
                if hr_dir.is_dir() and lr2_dir.is_dir() and lr4_dir.is_dir():
                    triplets = []
                    for i in range(1, 24):
                        hr_match = list(hr_dir.glob(f"HR_GT_{i}.*"))
                        l2_match = list(lr2_dir.glob(f"LR_256_{i}.*"))
                        l4_match = list(lr4_dir.glob(f"LR_128_{i}.*"))
                        if hr_match and l2_match and l4_match:
                            triplets.append((hr_match[0], l2_match[0], l4_match[0]))
                    if triplets:
                        return f"Dataset officiel ({base})", triplets

            # Cas C : jeu de démonstration généré localement si Images_TP2_EXO6_SR absent
            demo_dir = OUT_DIR / "exo6_demo_dataset"
            for sub in ("HR_GT_512x512", "LR_256x256", "LR_128x128"):
                (demo_dir / sub).mkdir(parents=True, exist_ok=True)
            seed_imgs = [
                "tp1_tp2_compteur_water_meter.jpg",
                "tp1_tp2_cameraman_gray.bmp",
                "tp1_exo4_exo5_peppers_color.bmp",
                "tp1_tp2_sample_barbara_portrait.bmp",
                "tp1_tp2_sample_houses_street.bmp",
            ]
            triplets = []
            for idx, fname in enumerate(seed_imgs, start=1):
                src = cv2.imread(str(IMG_DIR / fname), cv2.IMREAD_COLOR)
                if src is None:
                    continue
                hr = cv2.resize(src, (512, 512), interpolation=cv2.INTER_CUBIC)
                l2 = cv2.resize(hr, (256, 256), interpolation=cv2.INTER_AREA)
                l4 = cv2.resize(hr, (128, 128), interpolation=cv2.INTER_AREA)
                p_hr = demo_dir / "HR_GT_512x512" / f"HR_GT_{idx}.png"
                p_l2 = demo_dir / "LR_256x256" / f"LR_256_{idx}.png"
                p_l4 = demo_dir / "LR_128x128" / f"LR_128_{idx}.png"
                cv2.imwrite(str(p_hr), hr)
                cv2.imwrite(str(p_l2), l2)
                cv2.imwrite(str(p_l4), l4)
                triplets.append((p_hr, p_l2, p_l4))
            return "Jeu synthétique de démonstration (Images_TP2_EXO6_SR absent)", triplets

        dataset_label, sr_triplets = discover_sr_dataset()
        print(f"Source utilisée : {dataset_label} ({len(sr_triplets)} triplets d'images)")
        """),
        code_cell(r"""
        # Métriques PSNR et SSIM (Wang et al. 2004, sans dépendance externe)
        def calculate_psnr(hr_gt, hr_pred):
            mse = np.mean((hr_gt.astype(np.float64) - hr_pred.astype(np.float64)) ** 2)
            return 100.0 if mse == 0 else 10.0 * math.log10((255.0 ** 2) / mse)

        def calculate_ssim(img1, img2):
            a = img1.astype(np.float64)
            b = img2.astype(np.float64)
            if a.ndim == 3:
                return float(np.mean([calculate_ssim(a[:, :, c], b[:, :, c]) for c in range(a.shape[2])]))
            c1 = (0.01 * 255) ** 2
            c2 = (0.03 * 255) ** 2
            mu1 = cv2.GaussianBlur(a, (11, 11), 1.5)
            mu2 = cv2.GaussianBlur(b, (11, 11), 1.5)
            mu1_sq, mu2_sq, mu1_mu2 = mu1 * mu1, mu2 * mu2, mu1 * mu2
            s1_sq = cv2.GaussianBlur(a * a, (11, 11), 1.5) - mu1_sq
            s2_sq = cv2.GaussianBlur(b * b, (11, 11), 1.5) - mu2_sq
            s12 = cv2.GaussianBlur(a * b, (11, 11), 1.5) - mu1_mu2
            num = (2.0 * mu1_mu2 + c1) * (2.0 * s12 + c2)
            den = (mu1_sq + mu2_sq + c1) * (s1_sq + s2_sq + c2)
            return float(np.mean(num / den))

        # 2) Benchmark OpenCV : 2x (256->512), 4x direct (128->512), double 2x (128->256->512)
        interp_methods = [
            ("Plus proche voisin", cv2.INTER_NEAREST),
            ("Bilinéaire", cv2.INTER_LINEAR),
            ("Bicubique", cv2.INTER_CUBIC),
        ]

        summary = {}
        for m_name, m_flag in interp_methods:
            for mode in ("2x (256->512)", "4x direct (128->512)", "Double 2x (128->256->512)"):
                summary[(m_name, mode)] = {"psnr": [], "ssim": []}

        for p_hr, p_l2, p_l4 in sr_triplets:
            hr = cv2.imread(str(p_hr), cv2.IMREAD_COLOR)
            l2 = cv2.imread(str(p_l2), cv2.IMREAD_COLOR)
            l4 = cv2.imread(str(p_l4), cv2.IMREAD_COLOR)
            h_hr, w_hr = hr.shape[:2]

            for m_name, m_flag in interp_methods:
                pred_2x = cv2.resize(l2, (w_hr, h_hr), interpolation=m_flag)
                pred_4x = cv2.resize(l4, (w_hr, h_hr), interpolation=m_flag)
                mid_2x = cv2.resize(l4, (l2.shape[1], l2.shape[0]), interpolation=m_flag)
                pred_2x2x = cv2.resize(mid_2x, (w_hr, h_hr), interpolation=m_flag)

                for mode, pred in [("2x (256->512)", pred_2x), ("4x direct (128->512)", pred_4x), ("Double 2x (128->256->512)", pred_2x2x)]:
                    summary[(m_name, mode)]["psnr"].append(calculate_psnr(hr, pred))
                    summary[(m_name, mode)]["ssim"].append(calculate_ssim(hr, pred))

        print(f"{'Méthode':20s} | {'Échelle':25s} | {'PSNR moyen':>12s} | {'SSIM moyen':>12s}")
        print("-" * 78)
        for (m_name, mode), vals in summary.items():
            print(f"{m_name:20s} | {mode:25s} | {np.mean(vals['psnr']):10.3f} dB | {np.mean(vals['ssim']):12.4f}")
        """),
        code_cell(r"""
        # 3) Fonction personnelle d'interpolation bilinéaire 2x
        def super_resolution_bilineaire_2x(image, opencv_align=True):
            img = image.astype(np.float64)
            h, w = img.shape[:2]
            out_h, out_w = 2 * h, 2 * w

            if opencv_align:
                # Alignement exact sur les centres de pixels OpenCV: (i + 0.5)/2 - 0.5
                ys = np.clip((np.arange(out_h, dtype=np.float64) + 0.5) / 2.0 - 0.5, 0.0, h - 1.0)
                xs = np.clip((np.arange(out_w, dtype=np.float64) + 0.5) / 2.0 - 0.5, 0.0, w - 1.0)
            else:
                ys = np.clip(np.arange(out_h, dtype=np.float64) / 2.0, 0.0, h - 1.0)
                xs = np.clip(np.arange(out_w, dtype=np.float64) / 2.0, 0.0, w - 1.0)

            y0 = np.floor(ys).astype(np.int64)
            x0 = np.floor(xs).astype(np.int64)
            y1 = np.minimum(y0 + 1, h - 1)
            x1 = np.minimum(x0 + 1, w - 1)
            wy = (ys - y0)[:, None]
            wx = (xs - x0)[None, :]

            if img.ndim == 3:
                wy = wy[:, :, None]
                wx = wx[:, :, None]

            v00 = img[y0[:, None], x0[None, :]]
            v01 = img[y0[:, None], x1[None, :]]
            v10 = img[y1[:, None], x0[None, :]]
            v11 = img[y1[:, None], x1[None, :]]

            out = (
                (1.0 - wy) * (1.0 - wx) * v00
                + (1.0 - wy) * wx * v01
                + wy * (1.0 - wx) * v10
                + wy * wx * v11
            )
            return np.clip(np.round(out), 0, 255).astype(np.uint8)

        # Comparaison Bilinéaire Perso vs OpenCV INTER_LINEAR
        psnr_cv_list, psnr_perso_list, max_diffs = [], [], []
        for p_hr, p_l2, _ in sr_triplets:
            hr = cv2.imread(str(p_hr), cv2.IMREAD_COLOR)
            l2 = cv2.imread(str(p_l2), cv2.IMREAD_COLOR)
            b_cv = cv2.resize(l2, (hr.shape[1], hr.shape[0]), interpolation=cv2.INTER_LINEAR)
            b_perso = super_resolution_bilineaire_2x(l2, opencv_align=True)
            psnr_cv_list.append(calculate_psnr(hr, b_cv))
            psnr_perso_list.append(calculate_psnr(hr, b_perso))
            max_diffs.append(int(np.max(np.abs(b_cv.astype(np.int16) - b_perso.astype(np.int16)))))

        print(f"Bilinéaire 2x OpenCV PSNR moyen : {np.mean(psnr_cv_list):.4f} dB")
        print(f"Bilinéaire 2x Perso  PSNR moyen : {np.mean(psnr_perso_list):.4f} dB")
        print(f"Écart maximal pixel entre OpenCV et Perso : {max(max_diffs)} niveau(x) (arrondi)")
        """),
        code_cell(r"""
        # 4) Interpolation adaptative par Contours Pochoirs (Getreuer, 2009)
        def super_resolution_contour_stencils_2x(image, rho=0.5):
            '''
            Implémentation vectorisée de Contour Stencil Interpolation (Getreuer, SPIE 2009) :
            - 12 stencils orientés avec poids entiers normalisés par |S|
            - Norme l1 en YCrCb pour images couleur (Remarque 3) ou valeur absolue en NG
            - Lissage spatial G_rho sur TV(S) (Remarque 1)
            - 4 groupes de formules d'interpolation + moyennage des points milieux partagés
            '''
            h, w = image.shape[:2]
            if image.ndim == 3:
                feat = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb).astype(np.float64)
                img_f = image.astype(np.float64)
                pad_feat = np.pad(feat, ((1, 1), (1, 1), (0, 0)), mode="edge")
                diff_norm = lambda a, b: np.sum(np.abs(a - b), axis=2)
            else:
                img_f = image.astype(np.float64)
                pad_feat = np.pad(img_f, ((1, 1), (1, 1)), mode="edge")
                diff_norm = lambda a, b: np.abs(a - b)

            # Différences directionnelles sur la grille paddée (H+2, W+2)
            dh = diff_norm(pad_feat[:, :-1], pad_feat[:, 1:])       # (H+2, W+1)
            dv = diff_norm(pad_feat[:-1, :], pad_feat[1:, :])       # (H+1, W+2)
            da = diff_norm(pad_feat[:-1, :-1], pad_feat[1:, 1:])    # (H+1, W+1) main diag \
            db = diff_norm(pad_feat[1:, :-1], pad_feat[:-1, 1:])    # (H+1, W+1) anti-diag /

            ch, cw = h - 1, w - 1  # nombre de cellules (ch x cw)
            sl = lambda arr, r0, c0: arr[r0:r0 + ch, c0:c0 + cw]
            s2 = math.sqrt(2.0)

            # Définition des 12 stencils (arêtes dans le voisinage local 4x4)
            # Chaque entrée : (liste de (type_diff, r0, c0, poids), longueur_totale |S|)
            stencil_defs = [
                # 0: Vertical |
                ([("dv", 0, 1, 22), ("dv", 1, 1, 43), ("dv", 2, 1, 22),
                  ("dv", 0, 2, 22), ("dv", 1, 2, 43), ("dv", 2, 2, 22)], 174.0),
                # 1: Horizontal -
                ([("dh", 1, 0, 22), ("dh", 1, 1, 43), ("dh", 1, 2, 22),
                  ("dh", 2, 0, 22), ("dh", 2, 1, 43), ("dh", 2, 2, 22)], 174.0),
                # 2: Anti-diagonale / (45°)
                ([("db", 1, 0, 16), ("db", 0, 1, 16), ("db", 1, 1, 59),
                  ("db", 2, 1, 16), ("db", 1, 2, 16)], 123.0 * s2),
                # 3: Diagonale principale \ (-45°)
                ([("da", 1, 2, 16), ("da", 0, 1, 16), ("da", 1, 1, 59),
                  ("da", 2, 1, 16), ("da", 1, 0, 16)], 123.0 * s2),
                # 4: / douce (~26.6°)
                ([("db", 0, 0, 17), ("dh", 0, 1, 22), ("dh", 2, 0, 17),
                  ("db", 1, 1, 34), ("dh", 1, 2, 17), ("dh", 3, 1, 22), ("db", 2, 2, 17)], 78.0 + 68.0 * s2),
                # 5: \ raide (~63.4°)
                ([("da", 0, 2, 17), ("dv", 1, 3, 22), ("dv", 0, 1, 17),
                  ("da", 1, 1, 34), ("dv", 2, 2, 17), ("dv", 1, 0, 22), ("da", 2, 0, 17)], 78.0 + 68.0 * s2),
                # 6: \ douce (~-26.6°)
                ([("dh", 0, 1, 22), ("da", 0, 2, 17), ("dh", 1, 0, 17),
                  ("da", 1, 1, 34), ("dh", 2, 2, 17), ("da", 2, 0, 17), ("dh", 3, 1, 22)], 78.0 + 68.0 * s2),
                # 7: / raide (~63.4°)
                ([("db", 0, 0, 17), ("dv", 1, 0, 22), ("dv", 0, 2, 17),
                  ("db", 1, 1, 34), ("dv", 2, 1, 17), ("dv", 1, 3, 22), ("db", 2, 2, 17)], 78.0 + 68.0 * s2),
                # 8: Mixte /-H-/
                ([("db", 1, 0, 34), ("dh", 1, 1, 39), ("dh", 2, 1, 39), ("db", 1, 2, 34)], 78.0 + 68.0 * s2),
                # 9: Mixte \-H-\
                ([("da", 1, 0, 34), ("dh", 1, 1, 39), ("dh", 2, 1, 39), ("da", 1, 2, 34)], 78.0 + 68.0 * s2),
                # 10: Mixte \-V-\
                ([("da", 0, 1, 34), ("dv", 1, 1, 39), ("dv", 1, 2, 39), ("da", 2, 1, 34)], 78.0 + 68.0 * s2),
                # 11: Mixte /-V-/
                ([("db", 0, 1, 34), ("dv", 1, 1, 39), ("dv", 1, 2, 39), ("db", 2, 1, 34)], 78.0 + 68.0 * s2),
            ]

            diff_lookup = {"dh": dh, "dv": dv, "da": da, "db": db}
            tv_maps = np.empty((12, ch, cw), dtype=np.float64)
            for idx, (edges, norm_len) in enumerate(stencil_defs):
                acc = np.zeros((ch, cw), dtype=np.float64)
                for dkey, r0, c0, weight in edges:
                    acc += weight * sl(diff_lookup[dkey], r0, c0)
                tv_map = acc / norm_len
                if rho > 0.0:
                    tv_map = cv2.GaussianBlur(tv_map, (3, 3), sigmaX=rho, borderType=cv2.BORDER_REFLECT)
                tv_maps[idx] = tv_map

            best = np.argmin(tv_maps, axis=0)  # (ch, cw)

            # Coins des cellules (ch, cw, ...)
            tl = img_f[:-1, :-1]
            tr = img_f[:-1, 1:]
            bl = img_f[1:, :-1]
            br = img_f[1:, 1:]

            mid_n_bil = 0.5 * (tl + tr)
            mid_s_bil = 0.5 * (bl + br)
            mid_w_bil = 0.5 * (tl + bl)
            mid_e_bil = 0.5 * (tr + br)
            avg4 = 0.25 * (tl + tr + bl + br)
            diag_anti = 0.5 * (bl + tr)
            diag_main = 0.5 * (tl + br)

            n_val = mid_n_bil.copy()
            s_val = mid_s_bil.copy()
            w_val = mid_w_bil.copy()
            e_val = mid_e_bil.copy()
            x_val = avg4.copy()

            # Groupe B : 45° / (2) et -45° \ (3)
            m2 = (best == 2)
            m3 = (best == 3)
            x_val[m2] = diag_anti[m2]
            x_val[m3] = diag_main[m3]

            # Groupe C : 4, 5, 6, 7
            m4 = (best == 4)
            w_val[m4] = e_val[m4] = x_val[m4] = diag_anti[m4]

            m5 = (best == 5)
            n_val[m5] = s_val[m5] = x_val[m5] = diag_main[m5]

            m6 = (best == 6)
            w_val[m6] = e_val[m6] = x_val[m6] = diag_main[m6]

            m7 = (best == 7)
            n_val[m7] = s_val[m7] = x_val[m7] = diag_anti[m7]

            # Groupe D : 8, 9, 10, 11
            m8 = (best == 8)
            w_val[m8] = mid_n_bil[m8]
            e_val[m8] = mid_s_bil[m8]

            m9 = (best == 9)
            e_val[m9] = mid_n_bil[m9]
            w_val[m9] = mid_s_bil[m9]

            m10 = (best == 10)
            n_val[m10] = mid_e_bil[m10]
            s_val[m10] = mid_w_bil[m10]

            m11 = (best == 11)
            n_val[m11] = mid_w_bil[m11]
            s_val[m11] = mid_e_bil[m11]

            # Assemblage sur grille (2h, 2w) avec moyennage des milieux partagés entre cellules adjacentes
            out_shape = (2 * h, 2 * w) + (() if image.ndim == 2 else (image.shape[2],))
            out = np.zeros(out_shape, dtype=np.float64)

            # Pixels originaux aux coordonnées paires
            out[0:2 * h:2, 0:2 * w:2] = img_f
            # Centres de cellules X aux coordonnées (impair, impair)
            out[1:2 * h - 1:2, 1:2 * w - 1:2] = x_val

            # Milieux horizontaux (pair, impair) : moyenne entre S_{r-1,c} et N_{r,c}
            out[0, 1:2 * w - 1:2] = n_val[0]
            out[2 * h - 2, 1:2 * w - 1:2] = s_val[-1]
            if h > 2:
                out[2:2 * h - 2:2, 1:2 * w - 1:2] = 0.5 * (s_val[:-1] + n_val[1:])

            # Milieux verticaux (impair, pair) : moyenne entre E_{r,c-1} et W_{r,c}
            out[1:2 * h - 1:2, 0] = w_val[:, 0]
            out[1:2 * h - 1:2, 2 * w - 2] = e_val[:, -1]
            if w > 2:
                out[1:2 * h - 1:2, 2:2 * w - 2:2] = 0.5 * (e_val[:, :-1] + w_val[:, 1:])

            # Extrapolation propre du dernier pixel de bord droit et bas pour atteindre exactement 2h x 2w
            out[:, -1] = out[:, -2]
            out[-1, :] = out[-2, :]

            return np.clip(np.round(out), 0, 255).astype(np.uint8)

        # Évaluation comparative : Bilinéaire vs Bicubique vs Contours Pochoirs (2x et double 2x -> 4x)
        cs_2x_psnr, cs_2x_ssim = [], []
        bic_2x_psnr, bic_2x_ssim = [], []
        cs_4x_psnr, cs_4x_ssim = [], []
        bic_4x_psnr, bic_4x_ssim = [], []

        sample_vis = None
        for idx, (p_hr, p_l2, p_l4) in enumerate(sr_triplets):
            hr = cv2.imread(str(p_hr), cv2.IMREAD_COLOR)
            l2 = cv2.imread(str(p_l2), cv2.IMREAD_COLOR)
            l4 = cv2.imread(str(p_l4), cv2.IMREAD_COLOR)

            bic_2 = cv2.resize(l2, (hr.shape[1], hr.shape[0]), interpolation=cv2.INTER_CUBIC)
            cs_2 = super_resolution_contour_stencils_2x(l2, rho=0.5)

            bic_4 = cv2.resize(l4, (hr.shape[1], hr.shape[0]), interpolation=cv2.INTER_CUBIC)
            cs_4 = super_resolution_contour_stencils_2x(
                super_resolution_contour_stencils_2x(l4, rho=0.5), rho=0.5
            )

            bic_2x_psnr.append(calculate_psnr(hr, bic_2))
            bic_2x_ssim.append(calculate_ssim(hr, bic_2))
            cs_2x_psnr.append(calculate_psnr(hr, cs_2))
            cs_2x_ssim.append(calculate_ssim(hr, cs_2))

            bic_4x_psnr.append(calculate_psnr(hr, bic_4))
            bic_4x_ssim.append(calculate_ssim(hr, bic_4))
            cs_4x_psnr.append(calculate_psnr(hr, cs_4))
            cs_4x_ssim.append(calculate_ssim(hr, cs_4))

            if idx == 0:
                nn_4 = cv2.resize(l4, (hr.shape[1], hr.shape[0]), interpolation=cv2.INTER_NEAREST)
                bil_4 = cv2.resize(l4, (hr.shape[1], hr.shape[0]), interpolation=cv2.INTER_LINEAR)
                sample_vis = (hr, nn_4, bil_4, bic_4, cs_4)

        print(f"{'Méthode':28s} | {'Facteur':8s} | {'PSNR moyen':>12s} | {'SSIM moyen':>12s}")
        print("-" * 68)
        print(f"{'Bicubique (OpenCV)':28s} | {'2x':8s} | {np.mean(bic_2x_psnr):10.3f} dB | {np.mean(bic_2x_ssim):12.4f}")
        print(f"{'Contours Pochoirs (Perso)':28s} | {'2x':8s} | {np.mean(cs_2x_psnr):10.3f} dB | {np.mean(cs_2x_ssim):12.4f}")
        print(f"{'Bicubique (OpenCV)':28s} | {'4x':8s} | {np.mean(bic_4x_psnr):10.3f} dB | {np.mean(bic_4x_ssim):12.4f}")
        print(f"{'Contours Pochoirs (2x2x)':28s} | {'4x':8s} | {np.mean(cs_4x_psnr):10.3f} dB | {np.mean(cs_4x_ssim):12.4f}")

        if sample_vis is not None:
            hr, nn_4, bil_4, bic_4, cs_4 = sample_vis
            # Zoom sur un patch central 160x160 pour observer la netteté des contours
            cy, cx = hr.shape[0] // 2, hr.shape[1] // 2
            crop = lambda im: im[cy - 80:cy + 80, cx - 80:cx + 80]
            show_images([
                ("HR Vérité Terrain (zoom)", crop(hr)),
                ("Plus proche voisin 4x", crop(nn_4)),
                ("Bilinéaire 4x", crop(bil_4)),
                ("Bicubique 4x", crop(bic_4)),
                ("Contours Pochoirs 4x", crop(cs_4)),
            ], cols=5)
        """),
        md_cell(r"""
        ### Analyse & Remarques (SR 4x vs Double 2x et Contours Pochoirs)

        - **Plus proche voisin vs Bilinéaire vs Bicubique :** Le plus proche voisin introduit un fort effet d'escalier (crénelage). Le bilinéaire adoucit les transitions, tandis que le bicubique offre généralement les meilleurs scores PSNR/SSIM parmi les méthodes linéaires classiques en exploitant un voisinage de 16 pixels.
        - **SR 4x direct vs Double 2x ($2\times$ puis $2\times$) :** Sur l'interpolation bilinéaire ou bicubique, l'application en cascade (double $2\times$) peut légèrement différer du $4\times$ direct à cause de l'accumulation d'arrondis et de rééchantillonnages successifs (et du décalage de phase entre grilles). En revanche, pour les méthodes adaptatives par pyramide (*pyramid magnification* comme les Contours Pochoirs), l'application récursive $2\times \to 2\times$ affine progressivement l'orientation locale des contours.
        - **Contours Pochoirs vs Bicubique :** Comme souligné par Getreuer (2009, Figure 6), l'interpolation par contours pochoirs privilégie la **cohérence directionnelle et la netteté des bords** sans effet d'escalier ni dépassement (*overshoot*). Note technique importante : la grille OpenCV `cv2.resize` utilise un alignement centré $(i+0.5)/s - 0.5$ tandis que la grille cellulaire directe place $v_{i,j}$ en $(2i, 2j)$ (décalage d'un demi-pixel HR), ce qui peut influencer le PSNR brut selon la méthode utilisée pour générer les paires `LR`/`HR_GT`.
        """),
    ])

    # Validate every generated notebook in memory right away
    for nb_rel, nb in notebooks.items():
        validate_notebook_dict(nb_rel, nb)

    return notebooks


# ---------------------------------------------------------------------------
# Phase 0: Discovery & Transactional Planning (Read-Only)
# ---------------------------------------------------------------------------
def build_workspace_plan(root_dir: Path, self_script: Optional[Path]) -> WorkspacePlan:
    if not root_dir.exists() or not root_dir.is_dir():
        raise TransactionError(f"Le répertoire cible n'existe pas : {root_dir}")
    if not os.access(root_dir, os.W_OK):
        raise TransactionError(f"Le répertoire cible n'est pas accessible en écriture : {root_dir}")

    # Prevent overwriting an already organized workspace
    existing_targets = [d for d in TARGET_TOP_DIRS if (root_dir / d).exists()]
    if existing_targets:
        raise TransactionError(
            "Des dossiers cibles existent déjà dans le répertoire : "
            + ", ".join(sorted(existing_targets))
            + ". Abandon préventif pour éviter toute modification partielle ou écrasement."
        )

    all_disk_files: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Ignore any leftover hidden transaction directory just in case
        dirnames[:] = sorted(d for d in dirnames if not d.startswith(".tai_txn_"))
        for fname in sorted(filenames):
            fpath = Path(dirpath) / fname
            if self_script is not None and fpath.resolve() == self_script:
                continue
            all_disk_files.append(fpath)

    if not all_disk_files:
        raise TransactionError(f"Aucun fichier trouvé dans {root_dir}.")

    plan = WorkspacePlan(root_dir=root_dir, self_script=self_script, original_files=all_disk_files)

    # Track destination -> sha256 to guarantee zero accidental overwrites
    dest_registry: Dict[str, str] = {}
    seen_image_hashes: Dict[str, str] = {}

    def register_dest(proposed_rel: str, sha: str, original_rel: str) -> Tuple[str, str]:
        if proposed_rel not in dest_registry:
            dest_registry[proposed_rel] = sha
            return proposed_rel, "canonical"

        if dest_registry[proposed_rel] == sha:
            # Byte-identical duplicate -> preserve safely in archives/duplicates/
            dup_slug = sanitize_slug(str(Path(original_rel).with_suffix("")))
            ext = Path(original_rel).suffix.lower()
            dup_rel = f"archives/duplicates/{dup_slug}{ext}"
            counter = 1
            while dup_rel in dest_registry:
                dup_rel = f"archives/duplicates/{dup_slug}_copy{counter}{ext}"
                counter += 1
            dest_registry[dup_rel] = sha
            return dup_rel, "duplicate_archived"

        # Content differs! Disambiguate cleanly without losing anything
        p = Path(proposed_rel)
        counter = 1
        while True:
            alt_rel = str(p.with_name(f"{p.stem}_alt{counter}{p.suffix}")).replace("\\", "/")
            if alt_rel not in dest_registry:
                dest_registry[alt_rel] = sha
                return alt_rel, "conflict_renamed"
            if dest_registry[alt_rel] == sha:
                dup_slug = sanitize_slug(str(Path(original_rel).with_suffix("")))
                dup_rel = f"archives/duplicates/{dup_slug}_alt{counter}{p.suffix.lower()}"
                dest_registry[dup_rel] = sha
                return dup_rel, "duplicate_archived"
            counter += 1

    # Prioritize canonical roots (e.g. root PDFs before '(1)', Images/ before others)
    def sort_priority(fpath: Path) -> Tuple[int, str]:
        rel = fpath.relative_to(root_dir).as_posix()
        name_l = fpath.name.lower()
        has_dup_suffix = 1 if "(1)" in name_l or "copy" in name_l else 0
        in_images = 0 if rel.startswith("Images/") else 1
        return (has_dup_suffix, in_images, rel)

    for fpath in sorted(all_disk_files, key=sort_priority):
        rel = fpath.relative_to(root_dir).as_posix()
        sha = sha256_file(fpath)
        size = fpath.stat().st_size
        ext = fpath.suffix.lower()

        if ext in IMAGE_EXTENSIONS:
            mapped_img_name = map_image_filename(fpath.name, rel_hint=rel)
            proposed = f"{CONSOLIDATED_IMAGE_DIR}/{mapped_img_name}"
            dest_rel, status = register_dest(proposed, sha, rel)
            if status == "canonical":
                seen_image_hashes[sha] = dest_rel
            plan.ops.append(
                PlannedFileOp(
                    source_kind="disk",
                    source_path=fpath,
                    zip_member=None,
                    original_rel=rel,
                    dest_rel=dest_rel,
                    sha256=sha,
                    size_bytes=size,
                    status=status,
                )
            )
        else:
            fname_l = fpath.name.lower()
            if fname_l in NON_IMAGE_NAME_MAP:
                proposed = NON_IMAGE_NAME_MAP[fname_l]
            else:
                proposed = f"misc_preserved/{rel}"
            dest_rel, status = register_dest(proposed, sha, rel)
            plan.ops.append(
                PlannedFileOp(
                    source_kind="disk",
                    source_path=fpath,
                    zip_member=None,
                    original_rel=rel,
                    dest_rel=dest_rel,
                    sha256=sha,
                    size_bytes=size,
                    status=status,
                )
            )

    # Also inspect Images.zip to ensure NO unextracted images are missed
    images_zip = root_dir / "Images.zip"
    if images_zip.is_file():
        try:
            with zipfile.ZipFile(images_zip, "r") as zf:
                for info in zf.infolist():
                    if info.is_dir():
                        continue
                    member_path = Path(info.filename)
                    if member_path.name.startswith(".") or "__MACOSX" in member_path.parts:
                        continue
                    if member_path.suffix.lower() not in IMAGE_EXTENSIONS:
                        continue
                    with zf.open(info, "r") as stream:
                        sha, size = sha256_bytes_stream(stream)
                    if sha in seen_image_hashes:
                        continue
                    mapped_img_name = map_image_filename(member_path.name, rel_hint=info.filename)
                    proposed = f"{CONSOLIDATED_IMAGE_DIR}/{mapped_img_name}"
                    dest_rel, status = register_dest(proposed, sha, f"Images.zip::{info.filename}")
                    if status == "canonical" or status == "conflict_renamed":
                        seen_image_hashes[sha] = dest_rel
                        plan.ops.append(
                            PlannedFileOp(
                                source_kind="zip_entry",
                                source_path=images_zip,
                                zip_member=info.filename,
                                original_rel=f"Images.zip::{info.filename}",
                                dest_rel=dest_rel,
                                sha256=sha,
                                size_bytes=size,
                                status="zip_extracted",
                            )
                        )
        except zipfile.BadZipFile as exc:
            raise TransactionError(f"Archive Images.zip corrompue : {exc}") from exc

    # Verify all core required images for TP1 & TP2 were found
    consolidated_names = {
        Path(op.dest_rel).name
        for op in plan.ops
        if op.dest_rel.startswith(f"{CONSOLIDATED_IMAGE_DIR}/")
    }
    missing_core = sorted(REQUIRED_CANONICAL_IMAGES - consolidated_names)
    if missing_core:
        raise TransactionError(
            "Images obligatoires manquantes pour TP1/TP2 : " + ", ".join(missing_core)
        )

    # Build and validate all 11 Jupyter notebooks in memory
    plan.notebooks = build_all_notebooks()

    # Build manifest & README
    image_mappings = [
        {
            "original": op.original_rel,
            "destination": op.dest_rel,
            "sha256": op.sha256,
            "size_bytes": op.size_bytes,
            "status": op.status,
        }
        for op in plan.ops
        if op.dest_rel.startswith(f"{CONSOLIDATED_IMAGE_DIR}/")
    ]
    plan.manifest_dict = {
        "root_dir": str(root_dir),
        "consolidated_image_dir": CONSOLIDATED_IMAGE_DIR,
        "total_source_files": len(all_disk_files),
        "total_planned_operations": len(plan.ops),
        "total_notebooks": len(plan.notebooks),
        "operations": [
            {
                "source_kind": op.source_kind,
                "original_rel": op.original_rel,
                "dest_rel": op.dest_rel,
                "sha256": op.sha256,
                "size_bytes": op.size_bytes,
                "status": op.status,
            }
            for op in plan.ops
        ],
    }

    readme_lines = [
        "# Module TAI — Travaux Pratiques TP1 & TP2 (Espace organisé)",
        "",
        "## Structure des dossiers",
        "- `tp1_tp2_images/` : Dossier unique consolidé contenant toutes les images des TP1 et TP2 avec nommage uniforme.",
        "- `tp1_labs/` : Solutions complètes du TP1 en Jupyter Notebooks (`TP1_Exo1` à `TP1_Exo5`) + dossier `outputs/`.",
        "- `tp2_labs/` : Solutions complètes du TP2 en Jupyter Notebooks (`TP2_Exo1` à `TP2_Exo6`, incluant le devoir noté et les contours pochoirs) + dossier `outputs/`.",
        "- `docs/` : Énoncés (`assignments/`), supports de cours (`courses/`), et article de référence (`references/`).",
        "- `reference_solutions/` : Anciens fichiers de correction préservés.",
        "- `archives/` : Archives originales (`.zip`) et doublons exacts archivés sans perte dans `duplicates/`.",
        "- `organization_manifest.json` : Table complète de traçabilité (chemins et empreintes SHA-256).",
        "",
        "## Correspondance principale des images",
        "| Image d'origine | Nouveau nom standardisé (`tp1_tp2_images/`) |",
        "|---|---|",
    ]
    for item in sorted(image_mappings, key=lambda x: x["destination"]):
        readme_lines.append(f"| `{item['original']}` | `{Path(item['destination']).name}` |")
    plan.readme_text = "\n".join(readme_lines) + "\n"

    # Check disk space (staging copy + overhead)
    total_bytes = sum(op.size_bytes for op in plan.ops)
    free_bytes = shutil.disk_usage(root_dir).free
    required_bytes = total_bytes + 50 * 1024 * 1024  # +50 MB safety buffer
    if free_bytes < required_bytes:
        raise TransactionError(
            f"Espace disque insuffisant : {free_bytes / (1024**2):.1f} Mo libres, "
            f"{required_bytes / (1024**2):.1f} Mo requis."
        )

    return plan


# ---------------------------------------------------------------------------
# Phase 1 & Phase 2: Transactional Execution (Staging -> Backup -> Swap -> Verify)
# ---------------------------------------------------------------------------
def create_txn_root(root_dir: Path) -> Path:
    parent = root_dir.parent
    if parent.exists() and os.access(parent, os.W_OK):
        return Path(tempfile.mkdtemp(prefix=f".tai_txn_{uuid.uuid4().hex[:8]}_", dir=str(parent)))
    return Path(tempfile.mkdtemp(prefix=f".tai_txn_{uuid.uuid4().hex[:8]}_", dir=str(root_dir)))


def execute_transaction(plan: WorkspacePlan, simulate_failure_at: Optional[str] = None) -> None:
    root_dir = plan.root_dir
    txn_root = create_txn_root(root_dir)
    staging_target = txn_root / "staging_target"
    backup_dir = txn_root / "backup_original"
    staging_target.mkdir(parents=True, exist_ok=True)
    backup_dir.mkdir(parents=True, exist_ok=True)

    moved_to_backup: List[Tuple[Path, Path]] = []
    placed_in_root: List[Path] = []

    def rollback() -> None:
        logger.warning("ROLLBACK enclenché : restauration de l'état d'origine...")
        # 1. Supprimer les éléments nouvellement placés dans root_dir
        for placed in reversed(placed_in_root):
            try:
                if placed.is_dir() and not placed.is_symlink():
                    shutil.rmtree(placed)
                elif placed.exists() or placed.is_symlink():
                    placed.unlink()
            except Exception as exc:
                logger.error("Erreur lors du nettoyage de %s : %s", placed, exc)

        # 2. Restaurer tous les éléments originaux depuis backup_dir
        for orig_path, bak_path in reversed(moved_to_backup):
            if bak_path.exists() and not orig_path.exists():
                shutil.move(str(bak_path), str(orig_path))

        logger.info("Rollback terminé : l'état d'origine de %s a été intégralement restauré.", root_dir)

    try:
        # -------------------------------------------------------------------
        # PHASE 1: Build complete target tree in isolated staging directory
        # -------------------------------------------------------------------
        logger.info("Phase 1 : Construction de la structure cible dans %s", staging_target)
        for rel_dir in (
            CONSOLIDATED_IMAGE_DIR,
            "tp1_labs/outputs",
            "tp2_labs/outputs",
            "docs/assignments",
            "docs/courses",
            "docs/references",
            "reference_solutions",
            "archives/duplicates",
        ):
            (staging_target / rel_dir).mkdir(parents=True, exist_ok=True)

        # Copy all disk files & extract any unextracted zip images
        for op in plan.ops:
            dst = staging_target / op.dest_rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if op.source_kind == "disk":
                shutil.copy2(op.source_path, dst)
            elif op.source_kind == "zip_entry" and op.zip_member is not None:
                with zipfile.ZipFile(op.source_path, "r") as zf:
                    with zf.open(op.zip_member, "r") as src_stream, dst.open("wb") as out_stream:
                        shutil.copyfileobj(src_stream, out_stream)
            else:
                raise TransactionError(f"Opération inconnue : {op}")

            actual_sha = sha256_file(dst)
            if actual_sha != op.sha256:
                raise TransactionError(
                    f"Échec de vérification SHA-256 en staging pour {op.dest_rel} "
                    f"(attendu {op.sha256}, obtenu {actual_sha})"
                )

        if simulate_failure_at == "staging":
            raise TransactionError("Panne simulée durant la phase de staging.")

        # Write all 11 Jupyter Notebooks
        for nb_rel, nb_dict in plan.notebooks.items():
            nb_path = staging_target / nb_rel
            nb_path.parent.mkdir(parents=True, exist_ok=True)
            nb_path.write_text(json.dumps(nb_dict, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        # Write README.md and organization_manifest.json
        (staging_target / "README.md").write_text(plan.readme_text, encoding="utf-8")
        (staging_target / "organization_manifest.json").write_text(
            json.dumps(plan.manifest_dict, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        # Verify staging completeness (100% of original hashes preserved + valid notebooks)
        staged_hashes = set()
        for fpath in staging_target.rglob("*"):
            if fpath.is_file():
                staged_hashes.add(sha256_file(fpath))
        expected_hashes = {op.sha256 for op in plan.ops}
        missing_hashes = expected_hashes - staged_hashes
        if missing_hashes:
            raise TransactionError(
                f"Incohérence staging : {len(missing_hashes)} empreinte(s) source manquante(s)."
            )

        for nb_rel in plan.notebooks:
            nb_disk = staging_target / nb_rel
            loaded_nb = json.loads(nb_disk.read_text(encoding="utf-8"))
            validate_notebook_dict(nb_rel, loaded_nb)

        logger.info("Phase 1 validée avec succès (%d fichiers + %d notebooks vérifiés).", len(plan.ops), len(plan.notebooks))

        # -------------------------------------------------------------------
        # PHASE 2: Guarded swap (backup originals -> move staged tree -> verify)
        # -------------------------------------------------------------------
        logger.info("Phase 2 : Sauvegarde de l'état d'origine et bascule atomique...")

        top_entries = sorted(root_dir.iterdir(), key=lambda p: p.name)
        for idx, entry in enumerate(top_entries):
            if entry.name.startswith(".tai_txn_"):
                continue
            if plan.self_script is not None and entry.resolve() == plan.self_script:
                continue
            bak_path = backup_dir / entry.name
            shutil.move(str(entry), str(bak_path))
            moved_to_backup.append((entry, bak_path))
            if simulate_failure_at == "backup_move" and idx == 0:
                raise TransactionError("Panne simulée durant le déplacement vers backup.")

        staged_entries = sorted(staging_target.iterdir(), key=lambda p: p.name)
        for idx, staged_item in enumerate(staged_entries):
            dest_item = root_dir / staged_item.name
            shutil.move(str(staged_item), str(dest_item))
            placed_in_root.append(dest_item)
            if simulate_failure_at == "target_move" and idx == 0:
                raise TransactionError("Panne simulée durant le déplacement des cibles.")

        if simulate_failure_at == "post_verify":
            raise TransactionError("Panne simulée durant la vérification post-commit.")

        # Post-commit verification in root_dir
        img_dir = root_dir / CONSOLIDATED_IMAGE_DIR
        if not img_dir.is_dir():
            raise TransactionError(f"Dossier consolidé absent après commit : {img_dir}")

        for op in plan.ops:
            final_file = root_dir / op.dest_rel
            if not final_file.is_file():
                raise TransactionError(f"Fichier manquant après commit : {final_file}")
            if sha256_file(final_file) != op.sha256:
                raise TransactionError(f"Corruption SHA-256 détectée après commit : {final_file}")

        for nb_rel in plan.notebooks:
            nb_final = root_dir / nb_rel
            if not nb_final.is_file():
                raise TransactionError(f"Notebook manquant après commit : {nb_final}")
            validate_notebook_dict(nb_rel, json.loads(nb_final.read_text(encoding="utf-8")))

        if not (root_dir / "tp1_labs" / "outputs").is_dir() or not (root_dir / "tp2_labs" / "outputs").is_dir():
            raise TransactionError("Les sous-dossiers 'outputs' de TP1/TP2 n'ont pas été créés.")

        logger.info("Phase 2 vérifiée avec succès. Suppression du dossier temporaire de transaction.")

    except BaseException:
        rollback()
        raise
    finally:
        # Clean up staging/backup container cleanly if rollback succeeded or commit succeeded
        if txn_root.exists():
            # Safety guard: only remove backup_dir if all original entries are back or commit succeeded
            backup_remaining = [p for _, p in moved_to_backup if p.exists()]
            if not backup_remaining or all((root_dir / op.dest_rel).exists() for op in plan.ops):
                shutil.rmtree(txn_root, ignore_errors=True)
            else:
                logger.error("Attention : certains fichiers de backup subsistent dans %s", backup_dir)


# ---------------------------------------------------------------------------
# Dry-Run Summary & CLI Entry Point
# ---------------------------------------------------------------------------
def print_plan_summary(plan: WorkspacePlan) -> None:
    img_ops = [op for op in plan.ops if op.dest_rel.startswith(f"{CONSOLIDATED_IMAGE_DIR}/")]
    dup_ops = [op for op in plan.ops if op.status == "duplicate_archived"]
    conf_ops = [op for op in plan.ops if op.status == "conflict_renamed"]
    zip_ops = [op for op in plan.ops if op.status == "zip_extracted"]

    print("\n================ PLAN D'EXÉCUTION (ALL-OR-NOTHING) ================")
    print(f"Racine cible               : {plan.root_dir}")
    print(f"Fichiers source découverts : {len(plan.original_files)}")
    print(f"Images consolidées         : {len(img_ops)} -> {CONSOLIDATED_IMAGE_DIR}/")
    print(f"Images extraites du ZIP    : {len(zip_ops)}")
    print(f"Doublons exacts archivés   : {len(dup_ops)} -> archives/duplicates/")
    print(f"Conflits résolus sans perte: {len(conf_ops)}")
    print(f"Notebooks générés (.ipynb) : {len(plan.notebooks)}")
    print("\nNotebooks :")
    for nb_path in sorted(plan.notebooks):
        print(f"  + {nb_path}")
    print("\nÉchantillon du renommage des images :")
    for op in sorted(img_ops, key=lambda x: x.dest_rel)[:12]:
        print(f"  {op.original_rel:35s} -> {op.dest_rel}")
    if len(img_ops) > 12:
        print(f"  ... ({len(img_ops) - 12} autres images)")
    print("===================================================================\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Organise le dossier TAI et génère les solutions Jupyter (.ipynb) pour TP1 et TP2 de manière transactionnelle."
    )
    parser.add_argument(
        "--root",
        type=str,
        default=None,
        help="Chemin du dossier TAI (par défaut: répertoire courant ou ~/Downloads/TAI).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Effectue toute la validation (fichiers, SHA-256, JSON/AST des notebooks) sans rien modifier sur le disque.",
    )
    parser.add_argument(
        "--simulate-failure-at",
        choices=["staging", "backup_move", "target_move", "post_verify"],
        default=None,
        help="Option de test : simule une panne à une étape donnée pour vérifier la restauration intégrale par rollback.",
    )
    args = parser.parse_args()

    root_dir = resolve_root_dir(args.root)
    self_script = Path(__file__).resolve() if "__file__" in globals() else None

    try:
        logger.info("Phase 0 : Validation préliminaire en lecture seule sur %s", root_dir)
        plan = build_workspace_plan(root_dir, self_script)
        print_plan_summary(plan)

        if args.dry_run:
            logger.info("Mode --dry-run activé : aucune modification effectuée sur le disque.")
            return 0

        execute_transaction(plan, simulate_failure_at=args.simulate_failure_at)
        logger.info("Succès total ! L'espace TAI a été organisé et les 11 notebooks sont prêts.")
        return 0

    except TransactionError as exc:
        logger.error("Transaction annulée proprement : %s", exc)
        return 1
    except KeyboardInterrupt:
        logger.error("Interruption utilisateur : rollback terminé.")
        return 130
    except Exception as exc:
        logger.exception("Erreur inattendue : rollback terminé (%s)", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
