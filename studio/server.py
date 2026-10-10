"""Headless ComfyUI for batch runs: start -> queue API graphs -> collect files -> stop (always, in finally).

The GPU is borrowed through the CastelOS GPU window (the local brain is unloaded first and restored after).
"""
from __future__ import annotations

import contextlib
import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Iterator

COMFY = Path("D:/Tools/ComfyUI")
ROOT = Path(__file__).resolve().parents[1]
PORT = 8189   # not the default 8188, so a ComfyUI started by hand is never touched


class Comfy:
    def __init__(self, port: int = PORT) -> None:
        self.base = f"http://127.0.0.1:{port}"
        self.client = uuid.uuid4().hex

    def _get(self, path: str):
        with urllib.request.urlopen(self.base + path, timeout=30) as r:
            return json.loads(r.read())

    def ready(self) -> bool:
        try:
            self._get("/system_stats")
            return True
        except Exception:  # noqa: BLE001
            return False

    def run(self, graph: dict, out_dir: Path, name: str, timeout: float = 900) -> list[Path]:
        body = json.dumps({"prompt": graph, "client_id": self.client}).encode()
        req = urllib.request.Request(self.base + "/prompt", data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                pid = json.loads(r.read())["prompt_id"]
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"ComfyUI rejected graph {name}: {e.read().decode()[:600]}") from e
        t0 = time.time()
        while time.time() - t0 < timeout:
            h = self._get(f"/history/{pid}")
            if pid in h:
                st = h[pid].get("status", {})
                if st.get("status_str") == "error":
                    raise RuntimeError(f"{name} failed: {json.dumps(st.get('messages', []))[:800]}")
                files = []
                for out in h[pid]["outputs"].values():
                    for im in out.get("images", []):
                        src = ROOT / "output" / im.get("subfolder", "") / im["filename"]
                        dst = out_dir / f"{name}{src.suffix}" if len(files) == 0 else out_dir / f"{name}_{len(files)}{src.suffix}"
                        out_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, dst)
                        files.append(dst)
                return files
            time.sleep(1.0)
        raise TimeoutError(f"{name}: no result in {timeout} s")


@contextlib.contextmanager
def comfy_server(reason: str, max_s: float = 3600) -> Iterator[Comfy]:
    sys.path.insert(0, "D:/CastelOS")
    from casteldazur.scripts.image_gpu_session import image_session

    with image_session("comfy-product-studio", reason=reason, max_s=max_s) as ok:
        if not ok:
            raise SystemExit("GPU window refused - try later")
        (ROOT / "output").mkdir(exist_ok=True)
        (ROOT / "input").mkdir(exist_ok=True)
        log = open(ROOT / "output" / "comfy_server.log", "a", encoding="utf-8")
        proc = subprocess.Popen(
            [sys.executable, str(COMFY / "main.py"), "--listen", "127.0.0.1", "--port", str(PORT),
             "--extra-model-paths-config", str(ROOT / "extra_model_paths.yaml"),
             "--output-directory", str(ROOT / "output"), "--input-directory", str(ROOT / "input"),
             "--preview-method", "none", "--disable-auto-launch"],
            cwd=str(COMFY), stdout=log, stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
        try:
            c = Comfy()
            t0 = time.time()
            while not c.ready():
                if proc.poll() is not None:
                    raise RuntimeError("ComfyUI exited at start, see output/comfy_server.log")
                if time.time() - t0 > 240:
                    raise TimeoutError("ComfyUI did not start in 240 s")
                time.sleep(2)
            yield c
        finally:   # borrow and return: the server (and its VRAM) goes away on every exit path
            proc.terminate()
            try:
                proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                proc.kill()
            log.close()
