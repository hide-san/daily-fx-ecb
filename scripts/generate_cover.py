"""
scripts/generate_cover.py  --pair <BASEQUOTE>
==============================================
Generate a 1280x640 PNG cover image for one currency pair dataset.

Design: fraction layout centred in the canvas so that a square crop of
the middle 640×640 px captures all information cleanly.

Visual elements
---------------
- Fraction layout: BASE code (navy) over QUOTE code (Kaggle blue)
- Fraction bar with full currency names as subtitle
- Decorative sparklines on both sides (outside the square crop zone)
- Trust badges inside the square crop zone:
    · Daily Update
    · N years of data   <- computed from ECB_START_DATE, no df needed
    · ML-ready
    · ECB Source
"""

import argparse
import textwrap
from datetime import date

import cairosvg

from common import (
    CURRENCY_META,
    ECB_START_DATE,
    append_github_summary,
    pair_output_dir,
    parse_pair,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _years_of_data() -> int:
    """Return the number of full years since ECB_START_DATE."""
    start = date.fromisoformat(ECB_START_DATE)
    return date.today().year - start.year


def _subtitle_font_size(text: str) -> int:
    """Return a font size that keeps the subtitle within ~580 px.

    Three discrete steps based on character count.
    """
    n = len(text)
    if n <= 32:
        return 20
    if n <= 42:
        return 17
    return 14


# ---------------------------------------------------------------------------
# SVG builder
# ---------------------------------------------------------------------------

def build_svg(base: str, quote: str) -> str:
    """Return a 1280x640 SVG string.

    Safe zone for square crop: x = 320 ... 960  (centred on x = 640).
    All badges and essential text are placed within this range.
    Sparklines are purely decorative and may extend outside it.
    """
    base_name  = CURRENCY_META.get(base,  {}).get("name", base)
    quote_name = CURRENCY_META.get(quote, {}).get("name", quote)
    subtitle   = f"{base_name}  \u00b7  {quote_name}"
    sfsize     = _subtitle_font_size(subtitle)
    years      = _years_of_data()
    this_year  = date.today().year

    return textwrap.dedent(f"""\
        <svg width="1280" height="640" viewBox="0 0 1280 640"
             xmlns="http://www.w3.org/2000/svg">

          <!-- Background -->
          <rect width="1280" height="640" fill="#FAFCFF"/>

          <!-- Top / bottom accent bars -->
          <rect x="0"   y="0"   width="1280" height="6" fill="#20BEFF"/>
          <rect x="0"   y="634" width="1280" height="6" fill="#D6F2FF"/>

          <!-- Decorative sparklines (outside square crop zone, purely visual) -->
          <polyline
            points="60,420 90,395 120,410 150,375 180,390 210,357 240,370 270,340 300,354 330,326"
            fill="none" stroke="#20BEFF" stroke-width="1.5"
            stroke-linejoin="round" stroke-linecap="round" opacity="0.22"/>
          <polyline
            points="950,326 980,340 1010,312 1040,330 1070,300 1100,317 1130,287 1160,302 1190,274 1220,257"
            fill="none" stroke="#20BEFF" stroke-width="1.5"
            stroke-linejoin="round" stroke-linecap="round" opacity="0.22"/>
          <polygon
            points="950,326 980,340 1010,312 1040,330 1070,300 1100,317 1130,287 1160,302 1190,274 1220,257 1220,500 950,500"
            fill="#20BEFF" opacity="0.04"/>

          <!-- Series label -->
          <text x="640" y="68"
                font-family="Georgia, 'Times New Roman', serif"
                font-size="13" fill="#20BEFF" letter-spacing="9"
                text-anchor="middle">D A I L Y  F X</text>

          <!-- Years range -->
          <text x="640" y="92"
                font-family="Georgia, 'Times New Roman', serif"
                font-size="12" fill="#C8E8F8"
                text-anchor="middle">1999 \u2013 {this_year}  \u00b7  {years} years of data</text>

          <!-- Base currency code (numerator) -->
          <text x="640" y="264"
                font-family="Georgia, 'Times New Roman', serif"
                font-size="196" font-weight="700"
                fill="#0A2540"
                text-anchor="middle">{base}</text>

          <!-- Fraction bar: thin line + thick bar -->
          <rect x="330" y="282" width="620" height="2"  rx="1" fill="#20BEFF"/>
          <rect x="330" y="290" width="620" height="6"  rx="2" fill="#20BEFF"/>

          <!-- Full names subtitle (centred, dynamic size) -->
          <text x="640" y="313"
                font-family="Georgia, 'Times New Roman', serif"
                font-size="{sfsize}" fill="#0097D6"
                text-anchor="middle">{subtitle}</text>

          <!-- Quote currency code (denominator) -->
          <text x="640" y="472"
                font-family="Georgia, 'Times New Roman', serif"
                font-size="196" font-weight="700"
                fill="#20BEFF"
                text-anchor="middle">{quote}</text>

          <!-- Trust badges — 2 badges centred on x=640, inside square crop zone -->
          <rect x="474" y="493" width="136" height="28" rx="5"
                fill="#EBF8FF" stroke="#90D8F5" stroke-width="1"/>
          <text x="542" y="511"
                font-family="Georgia, 'Times New Roman', serif"
                font-size="12" fill="#0097D6"
                text-anchor="middle">\u25b2 Daily Update</text>

          <rect x="626" y="493" width="156" height="28" rx="5"
                fill="#EBF8FF" stroke="#90D8F5" stroke-width="1"/>
          <text x="704" y="511"
                font-family="Georgia, 'Times New Roman', serif"
                font-size="12" fill="#0097D6"
                text-anchor="middle">{years} years of data</text>


          <!-- Footer -->
          <text x="640" y="572"
                font-family="Georgia, 'Times New Roman', serif"
                font-size="13" fill="#C8E8F8"
                text-anchor="middle">\
European Central Bank \u00b7 Reference Rate \u00b7 1999\u2013present</text>

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
    args        = parser.parse_args()
    pair        = args.pair.upper()
    base, quote = parse_pair(pair)

    output_dir  = pair_output_dir(pair)
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
