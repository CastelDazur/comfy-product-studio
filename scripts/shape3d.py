"""Product photo -> 3D shape (Hunyuan3D 2.0 inside ComfyUI) -> .glb

Geometry only on purpose: the look comes later from the product photo itself (reference rendering), so the texture
never drifts away from the real upholstery.

  py -3.14 scripts/shape3d.py renders/smoke/sofa_seed7.png sofa
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

MODEL = "hunyuan3d-2\\hunyuan3d-dit-v2-0\\model.fp16.safetensors"


def graph(image: str, prefix: str, seed: int = 42) -> dict:
    return {
        "1": {"class_type": "LoadImage", "inputs": {"image": image}},
        "2": {"class_type": "Hy3DModelLoader", "inputs": {"model": MODEL, "attention_mode": "sdpa", "cublas_ops": False}},
        "3": {"class_type": "Hy3DGenerateMesh", "inputs": {"pipeline": ["2", 0], "image": ["1", 0],
                                                           "guidance_scale": 5.5, "steps": 50, "seed": seed,
                                                           "scheduler": "FlowMatchEulerDiscreteScheduler",
                                                           "force_offload": True}},
        "4": {"class_type": "Hy3DVAEDecode", "inputs": {"vae": ["2", 1], "latents": ["3", 0], "box_v": 1.01,
                                                        "octree_resolution": 384, "num_chunks": 8000, "mc_level": 0.0,
                                                        "mc_algo": "mc", "enable_flash_vdm": True, "force_offload": True}},
        "5": {"class_type": "Hy3DPostprocessMesh", "inputs": {"trimesh": ["4", 0], "remove_floaters": True,
                                                              "remove_degenerate_faces": True, "reduce_faces": True,
                                                              "max_facenum": 80000, "smooth_normals": False}},
        "6": {"class_type": "Hy3DExportMesh", "inputs": {"trimesh": ["5", 0], "filename_prefix": prefix,
                                                         "file_format": "glb", "save_file": True}},
    }


if __name__ == "__main__":
    src, name = Path(sys.argv[1]), sys.argv[2]
    if src.resolve() != (ROOT / "input" / src.name).resolve():
        shutil.copy2(src, ROOT / "input" / src.name)
    g = graph(src.name, f"3d/{name}")
    (ROOT / "workflows").mkdir(exist_ok=True)
    (ROOT / "workflows" / "03_photo_to_3d_shape.api.json").write_text(json.dumps(g, indent=1))
    with comfy_server("photo to 3D") as c:
        t0 = time.time()
        c.run(g, ROOT / "renders" / "3d", name, timeout=1200)
        print("done", round(time.time() - t0, 1), "s")
    print(sorted((ROOT / "output" / "3d").glob(f"{name}*.glb")))
