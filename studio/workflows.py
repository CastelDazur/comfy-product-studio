"""ComfyUI API-format graphs for FLUX.2 Klein 4B (distilled: 4 steps, cfg 1).

Every graph here is also saved as a JSON file in workflows/ so it can be dropped into ComfyUI and run by hand.
"""
from __future__ import annotations

UNET = "flux-2-klein-4b.safetensors"
CLIP = "qwen_3_4b.safetensors"
VAE = "flux2-vae.safetensors"


def _base(prompt: str, seed: int, w: int, h: int, steps: int, prefix: str) -> dict:
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": UNET, "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": CLIP, "type": "flux2"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": VAE}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["2", 0]}},
        "9": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["4", 0]}},
        "11": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
        "12": {"class_type": "Flux2Scheduler", "inputs": {"steps": steps, "width": w, "height": h}},
        "13": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "14": {"class_type": "EmptyFlux2LatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "15": {"class_type": "SamplerCustomAdvanced", "inputs": {
            "noise": ["13", 0], "guider": ["10", 0], "sampler": ["11", 0], "sigmas": ["12", 0],
            "latent_image": ["14", 0]}},
        "16": {"class_type": "VAEDecode", "inputs": {"samples": ["15", 0], "vae": ["3", 0]}},
        "17": {"class_type": "SaveImage", "inputs": {"images": ["16", 0], "filename_prefix": prefix}},
    }


def text_to_image(prompt: str, *, seed: int = 1, w: int = 1344, h: int = 1024, steps: int = 4,
                  prefix: str = "t2i") -> dict:
    g = _base(prompt, seed, w, h, steps, prefix)
    g["10"] = {"class_type": "CFGGuider", "inputs": {"model": ["1", 0], "positive": ["4", 0],
                                                    "negative": ["9", 0], "cfg": 1.0}}
    return g


def reference_edit(prompt: str, refs: list[str], *, seed: int = 1, w: int = 1344, h: int = 1024, steps: int = 4,
                   prefix: str = "edit") -> dict:
    """Same product, new scene: each reference image is encoded and attached to the conditioning
    (ReferenceLatent), so the model copies the product from the pixels instead of re-imagining it from text."""
    g = _base(prompt, seed, w, h, steps, prefix)
    cond = ["4", 0]
    for i, name in enumerate(refs):
        n = 100 + 10 * i
        g[str(n)] = {"class_type": "LoadImage", "inputs": {"image": name}}
        g[str(n + 1)] = {"class_type": "ImageScaleToTotalPixels",
                         "inputs": {"image": [str(n), 0], "upscale_method": "lanczos", "megapixels": 1.0,
                                    "resolution_steps": 16}}
        g[str(n + 2)] = {"class_type": "VAEEncode", "inputs": {"pixels": [str(n + 1), 0], "vae": ["3", 0]}}
        g[str(n + 3)] = {"class_type": "ReferenceLatent", "inputs": {"conditioning": cond, "latent": [str(n + 2), 0]}}
        cond = [str(n + 3), 0]
    g["10"] = {"class_type": "CFGGuider", "inputs": {"model": ["1", 0], "positive": cond,
                                                    "negative": ["9", 0], "cfg": 1.0}}
    return g
