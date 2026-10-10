"""Same product, many scenes: the product photo is the reference, the prompt describes only the room.

  py -3.14 scripts/scenes.py renders/smoke/sofa_seed7.png
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

KEEP = ("Place exactly this sofa from the reference image into the scene. Keep its shape, proportions, olive green "
        "velvet, cushions, arms and dark walnut legs identical. ")
SCENES = {
    "scandi_living": "Bright Scandinavian living room, white oak floor, linen curtains, a round jute rug, a small "
                     "oak coffee table with a ceramic vase, morning daylight from a large window, interior magazine photo.",
    "loft_evening": "Industrial loft with exposed brick wall and black steel windows, warm evening lamp light, "
                    "a leather pouf and a stack of books, polished concrete floor, editorial interior photo.",
    "classic_parisian": "Parisian apartment with white wall panelling and herringbone parquet, tall French windows, "
                        "a brass floor lamp, a marble side table, soft afternoon light, luxury catalogue photo.",
}

if __name__ == "__main__":
    src = Path(sys.argv[1])
    shutil.copy2(src, ROOT / "input" / src.name)
    with comfy_server("product scenes") as c:
        for name, room in SCENES.items():
            g = reference_edit(KEEP + room, [src.name], seed=11, prefix=name)
            (ROOT / "workflows" / "02_product_in_scene_reference.api.json").write_text(json.dumps(g, indent=1))
            t0 = time.time()
            print(c.run(g, ROOT / "renders" / "scenes", name), round(time.time() - t0, 1), "s", flush=True)
