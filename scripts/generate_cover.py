"""
scripts/generate_cover.py  --pair <BASEQUOTE>
==============================================
Generate a 1280x640 PNG cover image for one currency pair dataset.
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


def build_svg(base: str, quote: str) -> str:
    base_name  = CURRENCY_META.get(base,  {}).get("name", base)
    quote_name = CURRENCY_META.get(quote, {}).get("name", quote)
    meta_line  = f"{base_name.upper()}  \u00b7  {quote_name.upper()}"

    return textwrap.dedent(f"""\
        <svg width="1280" height="640" viewBox="0 0 1280 640"
             xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%"   stop-color="#042C53"/>
              <stop offset="100%" stop-color="#0d1117"/>
            </linearGradient>
          </defs>
          <rect width="1280" height="640" fill="url(#bg)"/>
          <circle cx="980"  cy="220" r="340" fill="#185FA5" opacity="0.12"/>
          <circle cx="1140" cy="380" r="260" fill="#1D9E75" opacity="0.10"/>
          <text x="80" y="110"
                font-family="ui-monospace, 'Courier New', monospace"
                font-size="28" font-weight="400"
                fill="#378ADD" opacity="0.7" letter-spacing="10">DAILY FX</text>
          <text x="80" y="380"
                font-family="ui-monospace, 'Courier New', monospace"
                font-size="220" font-weight="700"
                fill="#FFFFFF" letter-spacing="-6">{base}</text>
          <text x="730" y="380"
                font-family="ui-monospace, 'Courier New', monospace"
                font-size="220" font-weight="300"
                fill="#378ADD" opacity="0.5">/</text>
          <text x="848" y="380"
                font-family="ui-monospace, 'Courier New', monospace"
                font-size="220" font-weight="700"
                fill="#5DCAA5" letter-spacing="-6">{quote}</text>
          <line x1="80" y1="428" x2="1200" y2="428"
                stroke="#ffffff" stroke-width="1" opacity="0.08"/>
          <text x="80" y="484"
                font-family="ui-monospace, 'Courier New', monospace"
                font-size="26" font-weight="400"
                fill="#5F8BC4" letter-spacing="4">{meta_line}</text>
          <text x="80" y="530"
                font-family="ui-monospace, 'Courier New', monospace"
                font-size="22" font-weight="400"
                fill="#2C4A6E" letter-spacing="4">ECB REFERENCE RATE  \u00b7  1999 \u2013 PRESENT</text>
          <text x="1200" y="610"
                font-family="ui-monospace, 'Courier New', monospace"
                font-size="22" font-weight="400"
                fill="#1a2a3a" text-anchor="end" letter-spacing="4">ECB</text>
        </svg>
    """)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pair", required=True)
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
    print(f"Pair  : {pair}")
    print(f"Saved : {output_path}  ({size_kb:.1f} KB)")
    append_github_summary(f"| {pair} cover | {size_kb:.1f} KB |\n")


if __name__ == "__main__":
    main()
