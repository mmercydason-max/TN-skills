"""Generate placeholder logos (scales of justice + wordmark).

Run:  python scripts/make_logos.py
Replace Image/Logo.png and Image/inverseLogo.png with your own branding any time.
  Logo.png         -> dark artwork on white  (used in DOCX / PDF)
  inverseLogo.png  -> light artwork, transparent (used on the dark Streamlit page)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "Image"
FONT_CANDIDATES = [
    "C:/Windows/Fonts/times.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
]


def load_font(size: int):
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_scales(d: ImageDraw.ImageDraw, cx: int, top: int, size: int, color):
    w = max(3, size // 22)
    beam_y = top + size * 0.22
    half = size * 0.45
    d.line([(cx, top + size * 0.05), (cx, top + size * 0.92)], fill=color, width=w)   # pillar
    d.line([(cx - size * 0.28, top + size * 0.95), (cx + size * 0.28, top + size * 0.95)],
           fill=color, width=w)                                                        # base
    d.line([(cx - half, beam_y), (cx + half, beam_y)], fill=color, width=w)            # beam
    d.ellipse([cx - w * 1.6, top, cx + w * 1.6, top + w * 3.2], fill=color)            # finial
    for sx in (-half, half):                                                            # pans
        px = cx + sx
        pan_y = beam_y + size * 0.42
        d.line([(px, beam_y), (px - size * 0.2, pan_y)], fill=color, width=max(2, w // 2))
        d.line([(px, beam_y), (px + size * 0.2, pan_y)], fill=color, width=max(2, w // 2))
        d.pieslice([px - size * 0.24, pan_y - size * 0.14, px + size * 0.24, pan_y + size * 0.14],
                   0, 180, fill=color)


def make(path: Path, ink, background):
    W, H, icon = 900, 260, 200
    img = Image.new("RGBA", (W, H), background)
    d = ImageDraw.Draw(img)
    draw_scales(d, 160, 25, icon, ink)
    font = load_font(120)
    d.text((305, H / 2), "LegalEase", font=font, fill=ink, anchor="lm")
    img.save(path)
    print("wrote", path)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    make(OUT / "Logo.png", (20, 24, 40, 255), (255, 255, 255, 255))
    make(OUT / "inverseLogo.png", (255, 255, 255, 255), (0, 0, 0, 0))
