"""
scripts/generate_cover_local.py
================================
Local-only cover generator using Pillow (no Cairo required).

Design: white background, fraction layout centred in the canvas.
Only the two currency codes and the divider bar are shown.

Usage:
    python scripts/generate_cover_local.py            # all pairs in pairs.txt
    python scripts/generate_cover_local.py --pair USDJPY
"""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from common import load_pairs_file, pair_output_dir, parse_pair

W, H = 1280, 640
WHITE = "#FFFFFF"
NAVY = "#0A2540"
BLUE = "#20BEFF"

FONT_PATH = Path("C:/Windows/Fonts/georgiab.ttf")
FONT_SIZE = 218
BAR_H = 32


def make_cover(pair: str) -> Path:
    base, quote = parse_pair(pair)
    img = Image.new("RGB", (W, H), WHITE)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, W, BAR_H], fill=BLUE)
    draw.rectangle([0, H - BAR_H, W, H], fill=BLUE)

    font = ImageFont.truetype(str(FONT_PATH), FONT_SIZE)

    bx = draw.textlength(base, font=font)
    draw.text(((W - bx) / 2, 56), base, fill=NAVY, font=font)

    draw.rectangle([330, 300, 950, 310], fill=BLUE)

    qx = draw.textlength(quote, font=font)
    draw.text(((W - qx) / 2, 316), quote, fill=BLUE, font=font)

    output_dir = pair_output_dir(pair)
    output_path = output_dir / f"{pair}.png"
    img.save(output_path, "PNG")
    size_kb = output_path.stat().st_size / 1024
    print(f"Saved : {output_path}  ({size_kb:.1f} KB)")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pair", help="Single pair code, e.g. USDJPY")
    args = parser.parse_args()

    if args.pair:
        pairs = [args.pair.upper()]
    else:
        pairs = load_pairs_file()

    for pair in pairs:
        make_cover(pair)


if __name__ == "__main__":
    main()
