"""Clay view (angle + shape from the 3D model) + product photo (materials) -> photoreal view from that angle.

  py -3.14 scripts/views.py renders/smoke/sofa_seed7.png renders/turntable
"""
from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from studio.server import comfy_server  # noqa: E402
from studio.workflows import reference_edit  # noqa: E402

PROMPT = ("Turn the grey 3D model in the first image into a real product photo. Keep the camera angle, framing, "
          "pose, shape and proportions of the first image exactly. Use the materials of the sofa in the second image: "
          "olive green velvet upholstery with its sheen, the same cushions, dark walnut legs. Seamless light grey "
          "studio background, soft window light, catalogue photography, sharp focus.")

PROMPT_CLAY_ONLY = ("Turn this grey 3D model into a real product photo. Keep the camera angle, framing, pose, shape and "
                    "proportions exactly. Upholstery: olive green crushed velvet with soft sheen, piped cushion edges. "
                    "Legs: tapered dark walnut wood. Seamless light grey studio background, soft window light, "
                    "catalogue photography, sharp focus.")
PROMPT_PHOTO_FIRST = ("Show the sofa from the first image from exactly the camera angle, framing and pose of the grey "
                      "3D model in the second image. Same olive green velvet, same cushions, same dark walnut legs. "
                      "Seamless light grey studio background, catalogue photography, sharp focus.")


def refs_for(mode: str, clay: str, photo: str) -> tuple[str, list[str]]:
    if mode == "clay_only":
        return PROMPT_CLAY_ONLY, [clay]
    if mode == "photo_first":
        return PROMPT_PHOTO_FIRST, [photo, clay]
    return PROMPT, [clay, photo]


if __name__ == "__main__":
    photo, clay_dir = Path(sys.argv[1]), Path(sys.argv[2])
    mode = sys.argv[3] if len(sys.argv) > 3 else "clay_first"
    only = sys.argv[4].split(",") if len(sys.argv) > 4 else None
    shutil.copy2(photo, ROOT / "input" / photo.name)
    views = [v for v in sorted(clay_dir.glob("view_*.png")) if not only or v.stem in only]
    for v in views:
        shutil.copy2(v, ROOT / "input" / f"clay_{v.name}")
    with comfy_server("product 360 views") as c:
        for v in views:
            prompt, refs = refs_for(mode, f"clay_{v.name}", photo.name)
            g = reference_edit(prompt, refs, seed=5, prefix=v.stem)
            (ROOT / "workflows" / f"04_clay_view_to_photo_{mode}.api.json").write_text(json.dumps(g, indent=1))
            t0 = time.time()
            print(c.run(g, ROOT / "renders" / f"views_{mode}", v.stem), round(time.time() - t0, 1), "s", flush=True)
