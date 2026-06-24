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
# A real Victron Lynx Distributor has exactly 4 MEGA-fuse positions. We draw the
# unit COMPACT (slots tightly pitched) so several units can be bolted together
# ("accoles") on the same + busbar. One 4-slot unit holds the MPPT fuses, a 2nd
# unit glued alongside holds the 2x 200A MEGA fuses feeding the MultiPlus.
def make_lynx(fn, n_slots=4, slot_labels=None, title="LYNX DISTRIBUTOR",
              bus_label="+ BUS 48V", holder_w=88, pitch=112, side=20, H=128):
    body_bot = H - 26
    W = side * 2 + holder_w + (n_slots - 1) * pitch
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # dark DIN enclosure
    d.rounded_rectangle([3, 3, W - 4, body_bot], radius=12, fill=(44, 47, 53), outline=(20, 22, 26), width=3)
    # red strip along the bottom = the + busbar the unit clamps onto
    d.rounded_rectangle([7, body_bot, W - 7, H - 4], radius=6, fill=(198, 30, 30))
    fb = load_font(13)
    if bus_label:
        d.text((14, body_bot + 4), bus_label, fill=(255, 235, 235), font=fb)
    centers = [side + holder_w // 2 + i * pitch for i in range(n_slots)]
    top, bot = 11, body_bot - 9
    fl = load_font(13)
    for i, cx in enumerate(centers):
        x0, x1 = cx - holder_w // 2, cx + holder_w // 2
        # clear MEGA fuse-holder body
        d.rounded_rectangle([x0, top, x1, bot], radius=7, fill=(206, 224, 236), outline=(120, 140, 152), width=2)
        # green status LED near the top
        d.ellipse([cx - 8, top + 7, cx + 8, top + 23], fill=(70, 210, 90), outline=(40, 130, 55), width=2)
        # two bolt terminals + brown fuse element
        ty = top + 36
        d.ellipse([x0 + 11, ty, x0 + 29, ty + 18], fill=(225, 227, 230), outline=(120, 124, 128), width=2)
        d.ellipse([x1 - 29, ty, x1 - 11, ty + 18], fill=(225, 227, 230), outline=(120, 124, 128), width=2)
        d.line([x0 + 20, ty + 9, x1 - 20, ty + 9], fill=(150, 110, 40), width=5)
        # per-slot rating label
        lbl = slot_labels[i] if (slot_labels and i < len(slot_labels)) else ""
        if lbl:
            tw = d.textlength(lbl, font=fl)
            d.text((cx - tw / 2, bot - 17), lbl, fill=(35, 48, 60), font=fl)
        # stud down onto the red + busbar
        d.line([cx, bot, cx, body_bot], fill=(225, 227, 230), width=6)
    ft = load_font(13)
    if title:
        tw = d.textlength(title, font=ft)
        d.text((W - tw - 14, body_bot + 4), title, fill=(255, 235, 235), font=ft)
    img.save(os.path.join(ASSETS, fn))
    print("gen", fn, img.size)

# unit 1 : MPPT fuses (3 used + 1 spare) ; unit 2 : 2x 200A MEGA for the MultiPlus.
# unit 2 sits left-most on the bus, so it carries the "+ BUS 48V" label.
make_lynx("lynx_fuses.png", n_slots=4, slot_labels=["125A", "50A", "50A", "libre"],
          title="LYNX DISTRIBUTOR", bus_label="")
make_lynx("lynx_mega.png", n_slots=2, slot_labels=["200A", "200A"],
          title="MEGA", bus_label="+ BUS 48V")

# ---------- 4. rebuild imgdata.json ----------
names = ["aiko_mono.png", "aiko_bifacial.png", "rs450_100.png", "mppt_150_35.png",
         "multiplus_10k.png", "pylontech_us5000.png", "cerbo_gx.png", "battery_switch.png",
         "lynx_fuses.png", "lynx_mega.png", "parafoudre_dc.png", "parafoudre_ac.png", "fusible_mega.png",
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
