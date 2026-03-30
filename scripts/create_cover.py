"""
scripts/create_cover.py  --pair <BASEQUOTE>
==============================================
Generate a 1280x640 PNG cover image for one currency pair dataset.

Design: white background, fraction layout centred in the canvas.
Only the two currency codes and the divider bar are shown -- no labels,
no footer, no subtitle.  Everything reads clearly at thumbnail size.

Square crop of the middle 640x640 px captures all content cleanly.
"""

import argparse
import textwrap

import cairosvg

from common import (
    append_github_summary,
    pair_output_dir,
    parse_pair,
)


def build_svg(base: str, quote: str) -> str:
    """Return a 1280x640 SVG string.

    Safe zone for square crop: x = 320 ... 960  (centred on x = 640).
    """
    return textwrap.dedent(f"""\
        <svg width="1280" height="640" viewBox="0 0 1280 640"
             xmlns="http://www.w3.org/2000/svg">

          <!-- Background -->
          <rect width="1280" height="640" fill="#FFFFFF"/>

          <!-- Top / bottom thick bars -->
          <rect x="0" y="0"   width="1280" height="32" fill="#20BEFF"/>
          <rect x="0" y="608" width="1280" height="32" fill="#20BEFF"/>

          <!-- Base currency code (numerator) -->
          <text x="640" y="284"
                font-family="Georgia, 'Times New Roman', serif"
                font-size="218" font-weight="700"
                fill="#0A2540" text-anchor="middle">{base}</text>

          <!-- Fraction bar -->
          <rect x="330" y="300" width="620" height="10" rx="3" fill="#20BEFF"/>

          <!-- Quote currency code (denominator) -->
          <text x="640" y="504"
                font-family="Georgia, 'Times New Roman', serif"
                font-size="218" font-weight="700"
                fill="#20BEFF" text-anchor="middle">{quote}</text>

        </svg>
    """)


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
