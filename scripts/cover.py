"""Portfolio cover: input photo | 8 views around the product | 3 room scenes, one sheet.

  py -3.14 scripts/cover.py -> renders/cover.jpg
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

R = Path(__file__).resolve().parents[1] / "renders"
W, H = 2400, 1500
sheet = Image.new("RGB", (W, H), (246, 246, 244))
d = ImageDraw.Draw(sheet)
big = ImageFont.truetype("arialbd.ttf", 52)
mid = ImageFont.truetype("arial.ttf", 28)
small = ImageFont.truetype("arialbd.ttf", 24)


def fit(p: Path, w: int, h: int) -> Image.Image:
    im = Image.open(p).convert("RGB")
    s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


d.text((60, 40), "One product photo -> 3D -> every angle and any room, in ComfyUI", font=big, fill=(20, 20, 20))
d.text((60, 110), "FLUX.2 Klein 4B + Hunyuan3D in ComfyUI, Blender turntable, colour lock to the photo. "
                  "Same sofa in every frame.", font=mid, fill=(80, 80, 80))

# left: input photo
sheet.paste(fit(R / "smoke/sofa_seed7.png", 700, 540), (60, 180))
d.text((60, 730), "INPUT: one product photo", font=small, fill=(30, 30, 30))

# right: 8 views 4x2
vw, vh, gx = 380, 260, 13   # 800 + 4*380 + 3*13 = 2359 < 2400 - 40 margin
for i in range(8):
    x = 800 + (i % 4) * (vw + gx)
    y = 180 + (i // 4) * (vh + gx)
    sheet.paste(fit(R / f"views_locked/view_{i:02d}.png", vw, vh), (x, y))
d.text((800, 730), "8 VIEWS FROM THE 3D SHAPE (360 degrees)", font=small, fill=(30, 30, 30))

# bottom: 3 scenes
sw, sh = 740, 560
for i, n in enumerate(("scandi_living", "loft_evening", "classic_parisian")):
    x = 60 + i * (sw + 20)
    sheet.paste(fit(R / f"scenes/{n}.png", sw, sh), (x, 790))
d.text((60, 1365), "SAME PRODUCT IN ROOMS (reference-locked, ~3 s per image on one RTX 5090)", font=small,
       fill=(30, 30, 30))
d.text((60, 1410), "Workflows ship as ComfyUI API JSON + a Python batch runner for the next product.", font=mid,
       fill=(80, 80, 80))
sheet.save(R / "cover.jpg", quality=92)
print(R / "cover.jpg")
