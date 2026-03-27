"""
scripts/create_pipeline_diagram.py
====================================
Generate docs/pipeline.png -- a simple pipeline flow diagram.

Run manually when the pipeline structure changes:
    python scripts/create_pipeline_diagram.py

Output
------
docs/pipeline.png
"""

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

DOCS_DIR = Path("docs")
OUTPUT_PATH = DOCS_DIR / "pipeline.png"

COLOR_BOX_DARK = "#185FA5"
COLOR_BOX_LIGHT = "#4A90C4"
COLOR_ARROW = "#555555"
COLOR_BG = "#FFFFFF"
COLOR_TEXT = "#FFFFFF"
COLOR_LABEL = "#333333"


def draw_box(ax, x, y, w, h, label, sublabel=None, color=COLOR_BOX_DARK):
    box = mpatches.FancyBboxPatch(
        (x - w / 2, y - h / 2),
        w,
        h,
        boxstyle="round,pad=0.02",
        facecolor=color,
        edgecolor="white",
        linewidth=1.5,
        zorder=3,
    )
    ax.add_patch(box)
    if sublabel:
        ax.text(
            x,
            y + 0.07,
            label,
            ha="center",
            va="center",
            fontsize=8,
            fontweight="bold",
            color=COLOR_TEXT,
            zorder=4,
        )
        ax.text(
            x,
            y - 0.1,
            sublabel,
            ha="center",
            va="center",
            fontsize=6.5,
            color=COLOR_TEXT,
            zorder=4,
            alpha=0.85,
        )
    else:
        ax.text(
            x,
            y,
            label,
            ha="center",
            va="center",
            fontsize=8,
            fontweight="bold",
            color=COLOR_TEXT,
            zorder=4,
        )


def draw_arrow(ax, x1, x2, y):
    ax.annotate(
        "",
        xy=(x2 - 0.01, y),
        xytext=(x1 + 0.01, y),
        arrowprops={
            "arrowstyle": "-|>",
            "color": COLOR_ARROW,
            "lw": 1.5,
        },
        zorder=2,
    )


def main():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 4.5)
    ax.axis("off")
    fig.patch.set_facecolor(COLOR_BG)

    # --- Section labels ---
    ax.text(
        5.5,
        4.2,
        "Daily FX ECB -- Pipeline Overview",
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
        color=COLOR_LABEL,
    )

    ax.text(0.55, 3.55, "Daily (weekdays 15:30 UTC)", fontsize=7.5, color=COLOR_LABEL, va="center")
    ax.text(0.55, 1.55, "Weekly (Mondays 16:00 UTC)", fontsize=7.5, color=COLOR_LABEL, va="center")

    # --- Daily pipeline ---
    y_daily = 2.85
    boxes_daily = [
        (1.1, "ECB API", "15:00 UTC"),
        (2.6, "fetch_ecb.py", "raw rates"),
        (4.1, "calc_pair.py", "cross rates"),
        (5.6, "validate_pair", "quality gate"),
        (7.1, "upload_dataset", "per pair"),
        (8.9, "Kaggle", "Dataset"),
    ]
    colors_daily = [
        "#4A90C4",
        COLOR_BOX_DARK,
        COLOR_BOX_DARK,
        COLOR_BOX_DARK,
        COLOR_BOX_DARK,
        "#2E7D32",
    ]
    w, h = 1.2, 0.55
    for (x, label, sub), color in zip(boxes_daily, colors_daily, strict=True):
        draw_box(ax, x, y_daily, w, h, label, sub, color=color)

    for i in range(len(boxes_daily) - 1):
        x1 = boxes_daily[i][0] + w / 2
        x2 = boxes_daily[i + 1][0] - w / 2
        draw_arrow(ax, x1, x2, y_daily)

    # --- Notebook pipeline ---
    y_nb = 0.95
    boxes_nb = [
        (2.1, "create_notebook", "*.py x 3 kinds"),
        (4.1, "create_utils", "fx_utils.py"),
        (6.1, "upload_notebook", "per pair/kind"),
        (8.9, "Kaggle", "Notebooks"),
    ]
    colors_nb = [
        COLOR_BOX_DARK,
        COLOR_BOX_DARK,
        COLOR_BOX_DARK,
        "#2E7D32",
    ]
    for (x, label, sub), color in zip(boxes_nb, colors_nb, strict=True):
        draw_box(ax, x, y_nb, w, h, label, sub, color=color)

    for i in range(len(boxes_nb) - 1):
        x1 = boxes_nb[i][0] + w / 2
        x2 = boxes_nb[i + 1][0] - w / 2
        draw_arrow(ax, x1, x2, y_nb)

    # --- Divider ---
    ax.axhline(
        y=1.95, xmin=0.03, xmax=0.97, color="#CCCCCC", linewidth=0.8, linestyle="--", zorder=1
    )

    plt.tight_layout(pad=0.3)
    fig.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight", facecolor=COLOR_BG)
    plt.close(fig)
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
