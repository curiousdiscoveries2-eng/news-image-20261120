#!/usr/bin/env python3
"""
World News in One Image — Friday, 20 November 2026.

Renders a single 1024x1024 front-page-style infographic that sums up the
world news of 20 November 2026, from the bundled data file data/news.json.

Bounty: https://make.fun/bounty/news-image-20261120
Requirements honoured:
  * output is one PNG of at most 1 MiB and at most 1024x1024 px
  * no network access at render time (all data + fonts are bundled)
  * deterministic: the same input always produces the same output bytes
  * writes the image to /output/entry.png (falls back to ./output/entry.png)

Usage:  python3 main.py [output_path]
Requires: Python 3.13, Pillow.
"""

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "news.json"
FONT_DIR = ROOT / "fonts"

W, H = 1024, 1024
MARGIN = 36

# Palette — classic broadsheet front page.
PAPER = (247, 243, 234)
INK = (20, 24, 31)
MUTED = (92, 96, 104)
ACCENT = (176, 32, 40)          # front-page red
NAVY = (16, 32, 58)             # hero panel
NAVY_INK = (240, 242, 246)
CARD = (255, 254, 249)
CARD_LINE = (214, 207, 192)

CATEGORY_COLORS = {
    "DIPLOMACY": (21, 101, 192),
    "JUSTICE": (106, 27, 154),
    "CONFLICT": (183, 28, 28),
    "ECONOMY": (0, 105, 92),
    "DISASTER": (230, 81, 0),
    "CLIMATE": (46, 125, 50),
    "HEALTH": (0, 131, 143),
    "ENERGY": (141, 110, 0),
}


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size)


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt, max_width: int):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    words, lines, cur = text.split(), [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if draw.textlength(trial, font=fnt) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(draw, xy, text, fnt, fill, max_width, line_gap):
    x, y = xy
    for line in wrap(draw, text, fnt, max_width):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += fnt.size + line_gap
    return y


def chip(draw, x, y, label, color, dark_bg=False):
    """Small category label with a coloured square bullet."""
    f = font("LiberationSans-Bold.ttf", 17)
    draw.rectangle([x, y + 2, x + 12, y + 14], fill=color)
    draw.text((x + 20, y), label, font=f, fill=color if not dark_bg else color)
    return draw.textlength(label, font=f) + 20


def render(data: dict) -> Image.Image:
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    inner_w = W - 2 * MARGIN

    # ---------- Header ----------
    d.text((MARGIN, 26), "THE DAY IN ONE PAGE", font=font("LiberationSans-Bold.ttf", 20),
           fill=ACCENT)
    d.text((MARGIN, 52), "WORLD NEWS", font=font("LiberationSerif-Bold.ttf", 74), fill=INK)
    date_f = font("LiberationSans-Bold.ttf", 24)
    date_txt = data["date_label"]
    d.text((W - MARGIN - d.textlength(date_txt, font=date_f), 78), date_txt,
           font=date_f, fill=INK)
    sub_f = font("LiberationSans-Regular.ttf", 19)
    sub_txt = "The biggest stories on Earth, at a glance"
    d.text((W - MARGIN - d.textlength(sub_txt, font=sub_f), 108), sub_txt,
           font=sub_f, fill=MUTED)
    d.rectangle([MARGIN, 148, W - MARGIN, 154], fill=INK)
    d.rectangle([MARGIN, 158, W - MARGIN, 161], fill=ACCENT)

    # ---------- Hero ----------
    hero = data["hero"]
    hy, hh = 176, 196
    d.rectangle([MARGIN, hy, W - MARGIN, hy + hh], fill=NAVY)
    hx = MARGIN + 26
    color = CATEGORY_COLORS.get(hero["category"], ACCENT)
    d.rectangle([hx, hy + 20, hx + 12, hy + 32], fill=(255, 193, 7))
    d.text((hx + 20, hy + 18), f'{hero["category"]}  ·  {hero["place"]}',
           font=font("LiberationSans-Bold.ttf", 18), fill=(255, 193, 7))
    y = draw_wrapped(d, (hx, hy + 46), hero["headline"],
                     font("LiberationSans-Bold.ttf", 33), NAVY_INK, inner_w - 52, 6)
    draw_wrapped(d, (hx, y + 4), hero["summary"],
                 font("LiberationSans-Regular.ttf", 20), (196, 205, 219), inner_w - 52, 5)

    # ---------- Story grid: 2 columns x 3 rows ----------
    stories = data["stories"]
    gx, gy = MARGIN, 388
    gap = 14
    card_w = (inner_w - gap) // 2
    card_h = 150
    for i, story in enumerate(stories):
        cx = gx + (i % 2) * (card_w + gap)
        cy = gy + (i // 2) * (card_h + gap)
        color = CATEGORY_COLORS.get(story["category"], ACCENT)
        d.rectangle([cx, cy, cx + card_w, cy + card_h], fill=CARD, outline=CARD_LINE, width=1)
        d.rectangle([cx, cy, cx + 7, cy + card_h], fill=color)
        tx = cx + 22
        tw = card_w - 38
        d.rectangle([tx, cy + 16, tx + 12, cy + 28], fill=color)
        d.text((tx + 20, cy + 14), f'{story["category"]}  ·  {story["place"]}',
               font=font("LiberationSans-Bold.ttf", 15), fill=color)
        y = draw_wrapped(d, (tx, cy + 40), story["headline"],
                         font("LiberationSans-Bold.ttf", 21), INK, tw, 4)
        draw_wrapped(d, (tx, y + 3), story["summary"],
                     font("LiberationSans-Regular.ttf", 16), MUTED, tw, 3)

    # ---------- Bottom briefs strip ----------
    by = gy + 3 * card_h + 2 * gap + 14
    bh = 90
    d.rectangle([MARGIN, by, W - MARGIN, by + bh], fill=INK)
    half = inner_w // 2
    for i, brief in enumerate(data["briefs"]):
        bx = MARGIN + i * half + 22
        bw = half - 40
        color = CATEGORY_COLORS.get(brief["category"], ACCENT)
        d.rectangle([bx, by + 16, bx + 12, by + 28], fill=color)
        d.text((bx + 20, by + 14), f'{brief["category"]}  ·  {brief["place"]}',
               font=font("LiberationSans-Bold.ttf", 15), fill=(255, 255, 255))
        draw_wrapped(d, (bx, by + 38), brief["text"],
                     font("LiberationSans-Regular.ttf", 16), (214, 218, 224), bw, 3)
    d.line([MARGIN + half, by + 12, MARGIN + half, by + bh - 12], fill=(70, 76, 88), width=1)

    # ---------- Footer ----------
    fy = by + bh + 14
    d.text((MARGIN, fy),
           "Sources: Open Chronicle · One Turn News · Euronews · YouTube 24h world digest — reporting of 20 Nov 2026.",
           font=font("LiberationSans-Regular.ttf", 15), fill=MUTED)
    d.text((MARGIN, fy + 22),
           "One image, generated offline by a program — see README.md.",
           font=font("LiberationSans-Regular.ttf", 15), fill=MUTED)
    return img


def main() -> None:
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    img = render(data)
    if len(sys.argv) > 1:
        out = Path(sys.argv[1])
    else:
        out = Path("/output/entry.png")
        try:
            out.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            out = ROOT / "output" / "entry.png"
            out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, format="PNG", optimize=True)
    print(f"Wrote {out} ({out.stat().st_size} bytes, {img.size[0]}x{img.size[1]})")


if __name__ == "__main__":
    main()
