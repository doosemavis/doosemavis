"""Render assets/info-card.svg: a neofetch-style panel whose lines fade in one by one."""
from __future__ import annotations

from profile_data import load_profile
from svg_common import (ASSETS, DIM, KEY_COLORS, PROMPT, TEXT, char_width, esc, require_fit,
                        svg_doc, window_frame, wrap, write_svg)

WIDTH = 490
FONT_SIZE = 12.5
LINE_HEIGHT = 21
PAD_X = 22
FIRST_BASELINE = 58
KEY_GAP_CHARS = 2
MIN_VALUE_CHARS = 12  # the value column must keep at least this many characters
SWATCH_W, SWATCH_H = 26, 14
STAGGER = 0.12
START_DELAY = 0.4
CSS = (
    "@keyframes line { from { opacity: 0; transform: translateX(-6px); } }\n"
    ".ln { animation: line .35s ease-out both; }"
)


def _text(x: float, y: float, fill: str, text: str, bold: bool = False) -> str:
    weight = ' font-weight="bold"' if bold else ""
    return f'<text x="{x:.1f}" y="{y}" font-size="{FONT_SIZE}" fill="{fill}"{weight}>{esc(text)}</text>'


def _line(index: int, content: str) -> str:
    return f'<g class="ln" style="animation-delay:{START_DELAY + index * STAGGER:.2f}s">{content}</g>'


def _card_lines(prompt_user: str, rows: list[list[str]]) -> list[list[tuple]]:
    """Each output line as a list of (x, fill, text, bold) runs, wrapping long values."""
    cw = char_width(FONT_SIZE)
    longest_key = max((key for key, _ in rows), key=len)
    value_x = PAD_X + (len(longest_key) + KEY_GAP_CHARS) * cw
    value_chars = int((WIDTH - PAD_X - value_x) // cw)
    if value_chars < MIN_VALUE_CHARS:
        max_key = int((WIDTH - 2 * PAD_X) // cw) - KEY_GAP_CHARS - MIN_VALUE_CHARS
        raise ValueError(f"card key {longest_key!r} is {len(longest_key)} characters; max is {max_key}")
    lines = [[(PAD_X, PROMPT, prompt_user, True)], [(PAD_X, DIM, "─" * len(prompt_user), False)]]
    for i, (key, value) in enumerate(rows):
        color = KEY_COLORS[i % len(KEY_COLORS)]
        for j, part in enumerate(wrap(value, value_chars)):
            key_run = [(PAD_X, color, key, True)] if j == 0 else []
            lines.append(key_run + [(value_x, TEXT, part, False)])
    return lines


def render_info_card(prompt_user: str, rows: list[list[str]]) -> str:
    require_fit("prompt", prompt_user, FONT_SIZE, WIDTH - 2 * PAD_X)
    lines = _card_lines(prompt_user, rows)
    body = [
        _line(i, "".join(_text(x, FIRST_BASELINE + i * LINE_HEIGHT, fill, text, bold) for x, fill, text, bold in runs))
        for i, runs in enumerate(lines)
    ]
    swatch_y = FIRST_BASELINE + (len(lines) - 1) * LINE_HEIGHT + 14
    swatches = "".join(
        f'<rect x="{PAD_X + i * SWATCH_W}" y="{swatch_y}" width="{SWATCH_W}" height="{SWATCH_H}" fill="{color}"/>'
        for i, color in enumerate((*KEY_COLORS, TEXT, DIM))
    )
    body.append(_line(len(lines), swatches))
    height = swatch_y + SWATCH_H + 22
    frame = window_frame(WIDTH, height, f"{prompt_user}: ~")
    return svg_doc(WIDTH, height, frame + "".join(body), CSS)


def main() -> None:
    profile = load_profile()
    write_svg(ASSETS / "info-card.svg", render_info_card(profile["prompt"], profile["card"]))


if __name__ == "__main__":
    main()
