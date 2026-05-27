from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance
import math

ROOT = Path(__file__).resolve().parents[1]
LOGO = ROOT / "assets/logo-white.png"
OUT_DIR = ROOT / "assets/mp-workwear-logo-retouched-2026-05-27"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# x/y are center positions in original pixels. width is target emblem width.
# Workwear uses the M&P emblem only. The full legal-name logo becomes a white rectangle at chest size.
ITEMS = [
    {
        "src": "assets/mp-peter-hero-portraits-v2-2026-05-27-kie/selected_hero_peter_paved_workwear_official_logo.webp",
        "out": "selected_hero_peter_paved_workwear_clean_logo.webp",
        "erase": [{"x": 2055, "y": 625, "w": 260, "h": 170}, {"x": 2145, "y": 642, "w": 210, "h": 150}],
        "logos": [{"x": 2045, "y": 616, "w": 36, "rot": 0, "alpha": 0.70}],
    },
    {
        "src": "assets/mp-peter-hero-portraits-v2-2026-05-27-kie/selected_peter_portrait_professional_carport.webp",
        "out": "selected_peter_portrait_professional_carport_clean_logo.webp",
        "erase": [{"x": 1460, "y": 1580, "w": 260, "h": 330}],
        "logos": [{"x": 1460, "y": 1510, "w": 40, "rot": -3, "alpha": 0.80}],
    },
    {
        "src": "assets/mp-peter-hero-portraits-v2-2026-05-27-kie/selected_peter_portrait_professional_workshop.webp",
        "out": "selected_peter_portrait_professional_workshop_clean_logo.webp",
        "erase": [{"x": 1250, "y": 745, "w": 180, "h": 180}],
        "logos": [{"x": 1250, "y": 745, "w": 42, "rot": 2, "alpha": 0.80}],
    },
    {
        "src": "assets/mp-workwear-corrections-2026-05-26-kie/03_peter_red_hoodie_roofline.webp",
        "out": "03_peter_red_hoodie_roofline_clean_logo.webp",
        "erase": [{"x": 1320, "y": 720, "w": 190, "h": 180}],
        "logos": [{"x": 1320, "y": 720, "w": 42, "rot": -2, "alpha": 0.76}],
    },
    {
        "src": "assets/mp-workwear-corrections-2026-05-26-kie/02_peter_red_hoodie_post_level.webp",
        "out": "02_peter_red_hoodie_post_level_clean_logo.webp",
        "erase": [{"x": 1515, "y": 675, "w": 200, "h": 190}],
        "logos": [{"x": 1515, "y": 675, "w": 42, "rot": -4, "alpha": 0.76}],
    },
    {
        "src": "assets/mp-team-action-fix-2026-05-21-kie/03_team_vor_ort_zollstock_anzeichnen.webp",
        "out": "03_team_vor_ort_zollstock_anzeichnen_clean_logo.webp",
        "erase": [
            {"x": 2250, "y": 700, "w": 210, "h": 190},
            {"x": 1300, "y": 795, "w": 170, "h": 150},
        ],
        "logos": [
            {"x": 2250, "y": 700, "w": 42, "rot": -7, "alpha": 0.78},
            {"x": 1300, "y": 795, "w": 34, "rot": 5, "alpha": 0.66},
        ],
    },
]

def make_white_logo(width: int, alpha_scale: float) -> Image.Image:
    logo = Image.open(LOGO).convert("RGBA")
    # Crop to the chest-friendly M&P emblem; full legal text is unreadable at this size.
    logo = logo.crop((0, 0, 88, 147))
    r, g, b, a = logo.split()
    a = a.point(lambda p: int(p * alpha_scale))
    logo = Image.merge("RGBA", (Image.new("L", logo.size, 255), Image.new("L", logo.size, 255), Image.new("L", logo.size, 255), a))
    ratio = width / logo.width
    size = (width, max(1, int(logo.height * ratio)))
    logo = logo.resize(size, Image.Resampling.LANCZOS)
    # Tiny blur avoids sticker edge at web scale.
    return logo.filter(ImageFilter.GaussianBlur(0.16))

def fabric_patch(base: Image.Image, cx: int, cy: int, w: int, h: int, clone_dx=None, clone_dy: int = 0):
    # Clone neighboring fabric over the AI pseudo-logo. This is crude but much less visible than a flat fill.
    px0 = cx - w // 2
    py0 = cy - h // 2
    if clone_dx is None:
        clone_dx = -max(w, 80)
    sx0 = max(0, min(base.width - w, px0 + clone_dx))
    sy0 = max(0, min(base.height - h, py0 + clone_dy))
    patch = base.crop((sx0, sy0, sx0 + w, sy0 + h)).convert("RGBA")
    patch = patch.filter(ImageFilter.GaussianBlur(1.0))

    # Match average brightness/color roughly to target area.
    target = base.crop((max(0, px0), max(0, py0), min(base.width, px0 + w), min(base.height, py0 + h))).convert("RGB").resize((1, 1))
    source = patch.convert("RGB").resize((1, 1))
    tr, tg, tb = target.getpixel((0, 0))
    sr, sg, sb = source.getpixel((0, 0))
    dr, dg, db = tr - sr, tg - sg, tb - sb
    r, g, b, a = patch.split()
    r = r.point(lambda p: max(0, min(255, p + dr)))
    g = g.point(lambda p: max(0, min(255, p + dg)))
    b = b.point(lambda p: max(0, min(255, p + db)))
    patch = Image.merge("RGBA", (r, g, b, a))

    mask = Image.new("L", (w, h), 0)
    inner = Image.new("L", (max(1, w - 14), max(1, h - 14)), 210)
    mask.paste(inner, (7, 7))
    mask = mask.filter(ImageFilter.GaussianBlur(8))
    base.paste(patch, (px0, py0), mask)

def apply_logo(base: Image.Image, spec: dict):
    logo = make_white_logo(spec["w"], spec.get("alpha", 0.8))
    if spec.get("rot", 0):
        logo = logo.rotate(spec["rot"], expand=True, resample=Image.Resampling.BICUBIC)
    x = int(spec["x"] - logo.width / 2)
    y = int(spec["y"] - logo.height / 2)
    # Clear a bit wider/taller than the incoming logo first.
    fabric_patch(base, int(spec["x"]), int(spec["y"]), int(logo.width * 1.18), int(logo.height * 1.22))
    base.alpha_composite(logo, (x, y))

for item in ITEMS:
    base = Image.open(ROOT / item["src"]).convert("RGBA")
    for spec in item.get("erase", []):
        fabric_patch(base, int(spec["x"]), int(spec["y"]), int(spec["w"]), int(spec["h"]))
    for spec in item["logos"]:
        apply_logo(base, spec)
    out = OUT_DIR / item["out"]
    base.convert("RGB").save(out, "WEBP", quality=92, method=6)
    print(out.relative_to(ROOT))

# Build contact sheet.
thumb_w = 420
label_h = 38
pad = 24
cards = []
for idx, item in enumerate(ITEMS, 1):
    im = Image.open(OUT_DIR / item["out"]).convert("RGB")
    im.thumbnail((thumb_w, 260), Image.Resampling.LANCZOS)
    card = Image.new("RGB", (thumb_w, im.height + label_h), (244, 241, 234))
    card.paste(im, ((thumb_w - im.width) // 2, label_h))
    from PIL import ImageDraw
    d = ImageDraw.Draw(card)
    d.text((8, 10), f"{idx} {item['out'][:48]}", fill=(20, 20, 20))
    cards.append(card)
cols = 3
row_h = max(c.height for c in cards)
rows = math.ceil(len(cards) / cols)
sheet = Image.new("RGB", (cols * thumb_w + (cols + 1) * pad, rows * row_h + (rows + 1) * pad), (26, 23, 21))
for i, card in enumerate(cards):
    x = pad + (i % cols) * (thumb_w + pad)
    y = pad + (i // cols) * (row_h + pad)
    sheet.paste(card, (x, y))
sheet_path = OUT_DIR / "_contact_sheet_clean_logo.jpg"
sheet.save(sheet_path, quality=92)
print(sheet_path.relative_to(ROOT))
