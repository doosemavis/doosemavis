"""Local-only: render .portrait/prepped.png as an ASCII portrait that prints itself row by row."""
from __future__ import annotations

import sys

import numpy as np
from PIL import Image

from svg_common import ASSETS, BG, ROOT, TEXT, char_width, esc, svg_doc, write_svg

PREPPED = ROOT / ".portrait" / "prepped.png"
RAMP = " .`:-=+*cs#%@"  # sparse -> dense; glyphs are light on dark, so bright pixels get dense glyphs
COLS = 110
FONT_SIZE = 10
LINE_HEIGHT = 10
PAD = 10
ROW_SECONDS = 0.35
ROW_STAGGER = 0.05


def to_grid(gray: np.ndarray, cols: int = COLS) -> list[str]:
    h, w = gray.shape
    glyph_aspect = char_width(FONT_SIZE) / LINE_HEIGHT
    rows = max(1, round(cols * (h / w) * glyph_aspect))
    small = np.asarray(Image.fromarray(gray).resize((cols, rows), Image.LANCZOS), dtype=np.float32) / 255.0
    idx = np.clip(np.rint(small * (len(RAMP) - 1)), 0, len(RAMP) - 1).astype(int)
    return ["".join(RAMP[i] for i in row) for row in idx]


def render_ascii(rows: list[str]) -> str:
    cw = char_width(FONT_SIZE)
    row_w = len(rows[0]) * cw
    width = round(row_w + 2 * PAD)
    height = len(rows) * LINE_HEIGHT + 2 * PAD
    css = (
        f"@keyframes wipe {{ from {{ transform: translateX(-{row_w:.1f}px); }} }}\n"
        f"@keyframes cur {{ 0% {{ transform: translateX(-{row_w:.1f}px); opacity: 0; }} 1% {{ opacity: 1; }} "
        "98% { opacity: 1; } 100% { transform: translateX(0); opacity: 0; } }\n"
        f".w {{ animation: wipe {ROW_SECONDS}s linear both; }}\n"
        f".k {{ opacity: 0; animation: cur {ROW_SECONDS}s linear both; }}"
    )
    parts = [f'<rect width="{width}" height="{height}" rx="8" fill="{BG}"/>']
    for i, row in enumerate(rows):
        y = PAD + i * LINE_HEIGHT
        delay = f'style="animation-delay:{i * ROW_STAGGER:.2f}s"'
        parts.append(
            f'<text x="{PAD}" y="{y + LINE_HEIGHT - 2}" font-size="{FONT_SIZE}" fill="{TEXT}" '
            f'textLength="{row_w:.1f}" lengthAdjust="spacing" xml:space="preserve">{esc(row)}</text>'
        )
        # cover and cursor rest just past the row end, so the static frame shows the whole portrait
        parts.append(f'<rect class="w" x="{PAD + row_w:.1f}" y="{y}" width="{row_w + cw:.1f}" height="{LINE_HEIGHT}" fill="{BG}" {delay}/>')
        parts.append(f'<rect class="k" x="{PAD + row_w:.1f}" y="{y}" width="{cw:.1f}" height="{LINE_HEIGHT}" fill="{TEXT}" {delay}/>')
    return svg_doc(width, height, "".join(parts), css)


def main() -> int:
    if not PREPPED.is_file():
        print(f"make_ascii_svg: {PREPPED} not found; run scripts/prep_photo.py <photo> first", file=sys.stderr)
        return 1
    gray = np.asarray(Image.open(PREPPED).convert("L"))
    write_svg(ASSETS / "ascii-portrait.svg", render_ascii(to_grid(gray)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
