"""Hunyuan3D input: product on pure white, cropped square with margin, hard alpha edge."""
import sys
from PIL import Image
im=Image.open(sys.argv[1]); a=im.getchannel("A").point(lambda v:255 if v>128 else 0)
x0,y0,x1,y1=a.getbbox(); m=int(0.08*max(x1-x0,y1-y0))
w=max(x1-x0,y1-y0)+2*m; bg=Image.new("RGB",(w,w),"white")
rgb=im.convert("RGB"); bg.paste(rgb.crop((x0,y0,x1,y1)),((w-(x1-x0))//2,(w-(y1-y0))//2),a.crop((x0,y0,x1,y1)))
bg.resize((1024,1024),Image.LANCZOS).save(sys.argv[2]); print("ok",w)