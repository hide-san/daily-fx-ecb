"""
scripts/generate_cover.py  --pair <BASEQUOTE>
==============================================
Generate a 1280x640 PNG cover image for one currency pair dataset.

Design: dark navy background, fraction layout centred in the canvas.
Square crop of the middle 640x640 px captures all information cleanly.

Visual elements
---------------
- Dark navy background (#0A2540)
- "DAILY FX" brand label at top
- Fraction layout: BASE code (white) over QUOTE code (Kaggle blue #20BEFF)
- Thick Kaggle-blue fraction bar
- Full currency names as subtitle beneath the bar
- ECB footer
"""

import argparse
import textwrap

import cairosvg
from common import (
    CURRENCY_META,
    append_github_summary,
    pair_output_dir,
    parse_pair,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _subtitle_font_size(text: str) -> int:
    """Return a font size that keeps the subtitle within ~580 px.

    Three discrete steps based on character count.
    """
    n = len(text)
    if n <= 32:
        return 28
    if n <= 42:
        return 24
    return 20


# ---------------------------------------------------------------------------
# SVG builder
# ---------------------------------------------------------------------------


def build_svg(base: str, quote: str) -> str:
    """Return a 1280x640 SVG string.

    Safe zone for square crop: x = 320 ... 960  (centred on x = 640).
    All essential text is placed within this range.
    """
    base_name = CURRENCY_META.get(base, {}).get("name", base)
    quote_name = CURRENCY_META.get(quote, {}).get("name", quote)
    subtitle = f"{base_name}  /  {quote_name}"
    sfsize = _subtitle_font_size(subtitle)
    # Nudge subtitle up slightly for smaller font sizes so spacing feels even
    subtitle_y = 318 + (28 - sfsize)

    return textwrap.dedent(f"""\
        <svg width="1280" height="640" viewBox="0 0 1280 640"
             xmlns="http://www.w3.org/2000/svg">

          <!-- Background -->
          <rect width="1280" height="640" fill="#0A2540"/>

          <!-- Series label -->
          <text x="640" y="68"
                font-family="Georgia, 'Times New Roman', serif"
                font-size="22" letter-spacing="10"
                fill="#20BEFF" text-anchor="middle">DAILY FX</text>

          <!-- Base currency code (numerator) -->
          <text x="640" y="264"
                font-family="Georgia, 'Times New Roman', serif"
                font-size="208" font-weight="700"
                fill="#FFFFFF" text-anchor="middle">{base}</text>

          <!-- Fraction bar -->
          <rect x="330" y="282" width="620" height="10" rx="3" fill="#20BEFF"/>

          <!-- Full names subtitle -->
          <text x="640" y="{subtitle_y}"
                font-family="Georgia, 'Times New Roman', serif"
                font-size="{sfsize}" fill="#378ADD"
                text-anchor="middle">{subtitle}</text>

          <!-- Quote currency code (denominator) -->
          <text x="640" y="484"
                font-family="Georgia, 'Times New Roman', serif"
                font-size="208" font-weight="700"
                fill="#20BEFF" text-anchor="middle">{quote}</text>

          <!-- Footer -->
          <text x="640" y="578"
                font-family="Georgia, 'Times New Roman', serif"
                font-size="16" fill="#1A4060"
                text-anchor="middle">\
European Central Bank - Reference Rate - 1999-present</text>

        </svg>
    """)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a 1280x640 PNG cover image for one currency pair."
    )
    parser.add_argument("--pair", required=True, help="Pair code, e.g. USDJPY")
    args = parser.parse_args()
    pair = args.pair.upper()
    base, quote = parse_pair(pair)

    output_dir = pair_output_dir(pair)
    output_path = output_dir / f"{pair}.png"

    cairosvg.svg2png(
        bytestring=build_svg(base, quote).encode("utf-8"),
        write_to=str(output_path),
        output_width=1280,
        output_height=640,
    )

    size_kb = output_path.stat().st_size / 1024
    print(f"Pair  : {pair}  ({base} / {quote})")
    print(f"Saved : {output_path}  ({size_kb:.1f} KB)")
    append_github_summary(f"| {pair} cover | {size_kb:.1f} KB |\n")


if __name__ == "__main__":
    main()
