"""Product cut-out (RGBA) with Mask2Former ADE20K: the class mask of the product becomes the alpha channel.

  py -3.14 scripts/cutout.py renders/smoke/sofa_seed7.png sofa input/sofa_rgba.png
"""
from __future__ import annotations

import sys

import numpy as np
import torch
from PIL import Image, ImageFilter
from transformers import AutoImageProcessor, Mask2FormerForUniversalSegmentation

M2F = "D:/Models/Vision/mask2former-swin-large-ade-semantic"

if __name__ == "__main__":
    src, label, dst = sys.argv[1], sys.argv[2], sys.argv[3]
    img = Image.open(src).convert("RGB")
    proc = AutoImageProcessor.from_pretrained(M2F)
    model = Mask2FormerForUniversalSegmentation.from_pretrained(M2F).cuda().eval()
    try:
        with torch.no_grad():
            out = model(**{k: v.cuda() for k, v in proc(images=img, return_tensors="pt").items()})
        seg = proc.post_process_semantic_segmentation(out, target_sizes=[img.size[::-1]])[0].cpu().numpy()
        ids = [i for i, n in model.config.id2label.items() if label in n.lower()]
    finally:   # borrow and return
        del model
        torch.cuda.empty_cache()
    mask = np.isin(seg, ids).astype(np.uint8) * 255
    print("classes", ids, "coverage", round(mask.mean() / 255, 3))
    if mask.mean() < 2:
        raise SystemExit("product not found in the image")
    alpha = Image.fromarray(mask).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(1))
    rgba = img.copy()
    rgba.putalpha(alpha)
    rgba.save(dst)
