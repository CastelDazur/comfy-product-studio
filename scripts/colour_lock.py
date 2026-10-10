"""Colour lock: bring every generated view to the product photo's upholstery colour (LAB mean/std transfer on the
product pixels only; background untouched). Deterministic, so it cannot invent anything.

  py -3.14 scripts/colour_lock.py input/sofa_rgba.png renders/views_clay_only renders/views_locked
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image
from skimage import color


def product_pixels(rgb: np.ndarray) -> np.ndarray:
    """Coloured pixels = the product (backgrounds here are near-neutral grey)."""
    hsv = color.rgb2hsv(rgb)
    return (hsv[..., 1] > 0.18) & (hsv[..., 2] > 0.06)


if __name__ == "__main__":
    ref_path, src_dir, dst_dir = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    dst_dir.mkdir(parents=True, exist_ok=True)
    ref = np.asarray(Image.open(ref_path).convert("RGBA")).astype(float) / 255
    ref_lab = color.rgb2lab(ref[..., :3])[(ref[..., 3] > 0.5) & product_pixels(ref[..., :3])]
    mu_r, sd_r = ref_lab.mean(0), ref_lab.std(0)
    for p in sorted(src_dir.glob("*.png")):
        img = np.asarray(Image.open(p).convert("RGB")).astype(float) / 255
        m = product_pixels(img)
        lab = color.rgb2lab(img)
        mu, sd = lab[m].mean(0), lab[m].std(0)
        lab[m] = (lab[m] - mu) / np.maximum(sd, 1e-6) * sd_r + mu_r
        out = np.clip(color.lab2rgb(lab), 0, 1)
        Image.fromarray((out * 255).astype(np.uint8)).save(dst_dir / p.name)
        print(p.name, "L/a/b mean", np.round(mu, 1), "->", np.round(mu_r, 1))
