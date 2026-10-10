"""One text-to-image through ComfyUI to prove the stack (models, nodes, server lifecycle).

  py -3.14 scripts/smoke.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from studio.server import comfy_server  # noqa: E402
from studio.workflows import text_to_image  # noqa: E402

PROMPT = ("Studio product photo of a three-seat sofa with olive green velvet upholstery, rounded track arms, "
          "two loose seat cushions, thin dark walnut legs, front three-quarter view, seamless light grey "
          "background, soft large-window light, catalogue photography, sharp focus, true colours")

if __name__ == "__main__":
    g = text_to_image(PROMPT, seed=7, prefix="smoke")
    (ROOT / "workflows").mkdir(exist_ok=True)
    (ROOT / "workflows" / "01_product_photo_t2i.api.json").write_text(json.dumps(g, indent=1))
    with comfy_server("smoke test") as c:
        t0 = time.time()
        files = c.run(g, ROOT / "renders" / "smoke", "sofa_seed7")
        print(files, round(time.time() - t0, 1), "s")
