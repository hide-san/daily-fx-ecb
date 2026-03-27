"""
scripts/create_pipeline_diagram.py
====================================
Generate docs/pipeline.png -- a pipeline flow diagram.

Run manually when the pipeline structure changes:
    python scripts/create_pipeline_diagram.py

Output
------
docs/pipeline.png
"""

from pathlib import Path
from typing import cast

from PIL import Image, ImageDraw, ImageFont

DOCS_DIR = Path("docs")
OUTPUT_PATH = DOCS_DIR / "pipeline.png"

# Render at 3x then scale down for natural anti-aliasing
SCALE = 3
W, H = 1100 * SCALE, 460 * SCALE

# Colors
BG = (248, 250, 252)
SECT_BLUE = (239, 246, 255)
SECT_GREEN = (240, 253, 244)
BOX_DARK = (27, 74, 138)
BOX_MID = (43, 108, 176)
BOX_LIGHT = (66, 153, 225)
BOX_KAGGLE = (39, 103, 73)
BOX_KAGGLE2 = (56, 161, 105)
BOX_ECB = (66, 153, 225)
BOX_ECB2 = (74, 181, 242)
WHITE = (255, 255, 255)
ARROW_C = (148, 163, 184)
LABEL_DARK = (30, 41, 59)
LABEL_BLUE = (29, 78, 216)
LABEL_GREEN = (22, 101, 52)
FOOT_C = (148, 163, 184)
TEXT_SUB = (191, 219, 254)
TEXT_SUB2 = (147, 197, 253)
TEXT_GREEN = (187, 247, 208)
BORDER_BLUE = (191, 219, 254)
BORDER_GRN = (187, 247, 208)


def _font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (
        ["C:/Windows/Fonts/consola.ttf"]
        if mono
        else ["C:/Windows/Fonts/arialbd.ttf"]
        if bold
        else ["C:/Windows/Fonts/arial.ttf"]
    )
    for path in candidates:
        try:
            return ImageFont.truetype(path, size * SCALE)
        except OSError:
            pass
    return cast(ImageFont.FreeTypeFont, ImageFont.load_default())


def _rbox(
    draw: ImageDraw.ImageDraw,
    img: Image.Image,
    x: int,
    y: int,
    w: int,
    h: int,
    top: tuple[int, int, int],
    bot: tuple[int, int, int],
    r: int = 8,
) -> None:
    """Draw a gradient rounded rectangle onto img."""
    r_s = r * SCALE
    x2, y2, w2, h2 = x * SCALE, y * SCALE, w * SCALE, h * SCALE

    mask = Image.new("L", (w2, h2), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([0, 0, w2, h2], radius=r_s, fill=255)

    grad = Image.new("RGB", (w2, h2))
    gd = ImageDraw.Draw(grad)
    for i in range(h2):
        t = i / h2
        color = tuple(int(top[c] + (bot[c] - top[c]) * t) for c in range(3))
        gd.line([(0, i), (w2, i)], fill=color)

    img.paste(grad, (x2, y2), mask)
    draw.rounded_rectangle(
        [x2, y2, x2 + w2, y2 + h2],
        radius=r_s,
        fill=None,
        outline=WHITE,
        width=SCALE,
    )


def _text(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    t: str,
    size: int,
    color: tuple[int, int, int],
    bold: bool = False,
    mono: bool = False,
    anchor: str = "mm",
) -> None:
    draw.text(
        (x * SCALE, y * SCALE),
        t,
        fill=color,
        font=_font(size, bold=bold, mono=mono),
        anchor=anchor,
    )


def _arrow(draw: ImageDraw.ImageDraw, x1: int, y: int, x2: int) -> None:
    x1s, ys, x2s = x1 * SCALE, y * SCALE, x2 * SCALE
    draw.line([(x1s, ys), (x2s - 8 * SCALE, ys)], fill=ARROW_C, width=2 * SCALE)
    draw.polygon(
        [
            (x2s - 8 * SCALE, ys - 4 * SCALE),
            (x2s, ys),
            (x2s - 8 * SCALE, ys + 4 * SCALE),
        ],
        fill=ARROW_C,
    )


def _sect(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    h: int,
    fill: tuple[int, int, int],
    border: tuple[int, int, int],
) -> None:
    draw.rounded_rectangle(
        [x * SCALE, y * SCALE, (x + w) * SCALE, (y + h) * SCALE],
        radius=10 * SCALE,
        fill=fill,
        outline=border,
        width=SCALE,
    )


def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Title
    _text(draw, 550, 38, "Daily FX ECB -- Pipeline Overview", 22, LABEL_DARK, bold=True)

    # --- Daily section ---
    _sect(draw, 18, 60, 1064, 170, SECT_BLUE, BORDER_BLUE)
    _text(draw, 38, 80, "DAILY  -  weekdays 15:30 UTC", 11, LABEL_BLUE, bold=True, anchor="lm")

    boxes_d = [
        (48, 100, 140, 110, BOX_ECB2, BOX_ECB, "ECB API", "15:00 UTC", "EUR reference rates"),
        (
            228,
            100,
            140,
            110,
            BOX_MID,
            BOX_DARK,
            "fetch_ecb.py",
            "pulls raw rates",
            "all_currencies.csv",
        ),
        (408, 100, 140, 110, BOX_MID, BOX_DARK, "calc_pair.py", "cross rates", "PAIR.csv"),
        (588, 100, 140, 110, BOX_MID, BOX_DARK, "validate_pair", "quality gate", "5 checks"),
        (768, 100, 140, 110, BOX_MID, BOX_DARK, "upload_dataset", "Kaggle push", "per pair"),
        (912, 100, 152, 110, BOX_KAGGLE2, BOX_KAGGLE, "Kaggle", "Dataset", "24 pairs"),
    ]
    for x, y, w, h, top, bot, l1, l2, l3 in boxes_d:
        _rbox(draw, img, x, y, w, h, top, bot)
        cx = x + w // 2
        _text(draw, cx, y + 32, l1, 13, WHITE, bold=True)
        _text(draw, cx, y + 52, l2, 10, TEXT_SUB)
        _text(draw, cx, y + 68, l3, 9, TEXT_SUB2, mono=True)

    _arrow(draw, 190, 155, 226)
    _arrow(draw, 370, 155, 406)
    _arrow(draw, 550, 155, 586)
    _arrow(draw, 730, 155, 766)
    _arrow(draw, 910, 155, 910)

    # --- Weekly section ---
    _sect(draw, 18, 250, 1064, 170, SECT_GREEN, BORDER_GRN)
    _text(draw, 38, 270, "WEEKLY  -  Mondays 16:00 UTC", 11, LABEL_GREEN, bold=True, anchor="lm")

    boxes_n = [
        (
            118,
            292,
            160,
            110,
            BOX_MID,
            BOX_DARK,
            "create_notebook",
            "GS / EDA / Modeling",
            "*.ipynb per pair",
        ),
        (338, 292, 160, 110, BOX_MID, BOX_DARK, "create_utils", "shared utilities", "fx_utils.py"),
        (558, 292, 160, 110, BOX_MID, BOX_DARK, "upload_notebook", "Kaggle push", "max 3 parallel"),
        (828, 292, 152, 110, BOX_KAGGLE2, BOX_KAGGLE, "Kaggle", "Notebooks", "72 notebooks"),
    ]
    for x, y, w, h, top, bot, l1, l2, l3 in boxes_n:
        _rbox(draw, img, x, y, w, h, top, bot)
        cx = x + w // 2
        _text(draw, cx, y + 32, l1, 13, WHITE, bold=True)
        _text(draw, cx, y + 52, l2, 10, TEXT_SUB)
        _text(draw, cx, y + 68, l3, 9, TEXT_SUB2, mono=True)

    _arrow(draw, 280, 347, 336)
    _arrow(draw, 500, 347, 556)
    _arrow(draw, 720, 347, 826)

    # Footer
    _text(
        draw,
        550,
        443,
        "Source: European Central Bank (ECB)  -  github.com/hide-san/daily-fx-ecb",
        10,
        FOOT_C,
    )

    # Scale down for anti-aliasing
    out = img.resize((W // SCALE, H // SCALE), Image.Resampling.LANCZOS)
    out.save(OUTPUT_PATH, dpi=(192, 192))
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
