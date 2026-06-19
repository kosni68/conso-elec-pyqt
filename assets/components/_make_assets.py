# -*- coding: utf-8 -*-
"""Process extracted product photos + generate custom component images."""
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageColor
import os, base64, json

ASSETS = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ASSETS, "_raw2")

def load_font(size, bold=True):
    for n in (("arialbd.ttf" if bold else "arial.ttf"), "arial.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(n, size)
        except Exception:
            continue
    return ImageFont.load_default()

def trim(im, bg_is_white=True, thr=12):
    im = im.convert("RGB")
    ref = Image.new("RGB", im.size, (255, 255, 255) if bg_is_white else (0, 0, 0))
    diff = ImageChops.difference(im, ref)
    bbox = diff.getbbox()
    return im.crop(bbox) if bbox else im

# ---------- 1. process extracted product photos ----------
def proc(src, dst, maxw, white=True, pad=10):
    im = Image.open(os.path.join(RAW, src))
    im = trim(im, white)
    if white:
        # paste on white canvas with small padding for a clean look
        w, h = im.size
        canvas = Image.new("RGB", (w + 2 * pad, h + 2 * pad), (255, 255, 255))
        canvas.paste(im, (pad, pad))
        im = canvas
    w, h = im.size
    if w > maxw:
        im = im.resize((maxw, int(h * maxw / w)), Image.LANCZOS)
    im.save(os.path.join(ASSETS, dst), "PNG")
    print("proc", dst, im.size)

proc("S14_p70_715_205x349.png", "parafoudre_dc.png", 150)      # CITEL DS40-48DC
proc("S14_p57_622_541x740.png", "parafoudre_ac.png", 150)      # CITEL MDAC50VG-275
proc("S5_p35_216_321x196.png",  "fusible_mega.png", 170)       # Victron MEGA fuse holder

# ---------- 2. generate INVERSEUR DE SOURCE (rotary changeover) ----------
def make_inverseur(fn, W=300, H=300):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # enclosure
    d.rounded_rectangle([6, 6, W - 7, H - 7], radius=22, fill=(214, 217, 221), outline=(120, 124, 130), width=3)
    # corner screws
    for cx, cy in [(34, 34), (W - 34, 34), (34, H - 34), (W - 34, H - 34)]:
        d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(170, 174, 180), outline=(110, 114, 120), width=2)
        d.line([cx - 5, cy, cx + 5, cy], fill=(90, 94, 100), width=2)
    cx, cy, r = W // 2, H // 2 + 6, 78
    # dial face
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(245, 246, 248), outline=(150, 154, 160), width=3)
    # position marks I (left) 0 (top) II (right)
    f = load_font(30)
    d.text((cx - r - 2, cy - 16), "I", fill=(190, 30, 30), font=f)
    d.text((cx - 8, cy - r - 30), "0", fill=(60, 60, 60), font=f)
    d.text((cx + r - 14, cy - 16), "II", fill=(30, 120, 60), font=f)
    # knob
    kr = 50
    d.ellipse([cx - kr, cy - kr, cx + kr, cy + kr], fill=(40, 42, 46), outline=(20, 20, 22), width=2)
    # pointer toward II (installation)
    import math
    ang = math.radians(-35)
    px, py = cx + int(kr * 0.86 * math.cos(ang)), cy + int(kr * 0.86 * math.sin(ang))
    d.line([cx, cy, px, py], fill=(255, 210, 60), width=8)
    d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=(255, 210, 60))
    # title strip
    f2 = load_font(20)
    d.text((cx - 78, 18), "INVERSEUR", fill=(40, 44, 50), font=f2)
    img.save(os.path.join(ASSETS, fn))
    print("gen", fn, img.size)

make_inverseur("inverseur_source.png")

# ---------- 3. generate LYNX DISTRIBUTOR fuse-bank (sits on the + bus) ----------
def make_lynx(fn, W=1080, H=150, fracs=(0.21, 0.40, 0.58, 0.90)):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # dark DIN enclosure
    d.rounded_rectangle([4, 4, W - 5, H - 30], radius=14, fill=(44, 47, 53), outline=(20, 22, 26), width=3)
    # thin red strip along the very bottom = mounts on the + bus
    d.rounded_rectangle([10, H - 30, W - 10, H - 6], radius=6, fill=(198, 30, 30))
    f = load_font(15)
    d.text((22, H - 27), "+ BUS 48V", fill=(255, 235, 235), font=f)
    holder_w = 150
    for fr in fracs:
        midx = int(W * fr)
        x0, x1 = midx - holder_w // 2, midx + holder_w // 2
        # clear fuse holder body
        d.rounded_rectangle([x0, 18, x1, 96], radius=8, fill=(206, 224, 236), outline=(120, 140, 152), width=2)
        # two bolt terminals + fuse element
        d.ellipse([x0 + 14, 50, x0 + 38, 74], fill=(225, 227, 230), outline=(120, 124, 128), width=2)
        d.ellipse([x1 - 38, 50, x1 - 14, 74], fill=(225, 227, 230), outline=(120, 124, 128), width=2)
        d.line([x0 + 26, 62, x1 - 26, 62], fill=(150, 110, 40), width=5)
        # green status LED
        d.ellipse([midx - 9, 26, midx + 9, 44], fill=(70, 210, 90), outline=(40, 130, 55), width=2)
        # stud down to red bus strip
        d.line([midx, 96, midx, H - 30], fill=(225, 227, 230), width=6)
    ft = load_font(15)
    d.text((W - 250, H - 27), "LYNX DISTRIBUTOR", fill=(255, 235, 235), font=ft)
    img.save(os.path.join(ASSETS, fn))
    print("gen", fn, img.size)

make_lynx("lynx_fuses.png")

# ---------- 4. rebuild imgdata.json ----------
names = ["aiko_mono.png", "aiko_bifacial.png", "rs450_100.png", "mppt_150_35.png",
         "multiplus_10k.png", "pylontech_us5000.png", "cerbo_gx.png", "battery_switch.png",
         "lynx_fuses.png", "parafoudre_dc.png", "parafoudre_ac.png", "fusible_mega.png",
         "inverseur_source.png"]
data = {}
for n in names:
    p = os.path.join(ASSETS, n)
    b = base64.b64encode(open(p, "rb").read()).decode()
    im = Image.open(p)
    data[n] = {"w": im.size[0], "h": im.size[1], "b64": b}
    print(f"  {n:22} {im.size}  {len(b)//1024}KB")
json.dump(data, open(os.path.join(ASSETS, "_imgdata.json"), "w"))
print("total KB", sum(len(v["b64"]) for v in data.values()) // 1024)
