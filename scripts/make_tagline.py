"""Render assets/tagline.svg: a prompt that types `echo "<tagline>"` once, then blinks a cursor."""
from __future__ import annotations

from profile_data import load_profile
from svg_common import (ASSETS, BG, BORDER, PATH_BLUE, PROMPT, TEXT, char_width, esc, require_fit,
                        svg_doc, write_svg)

WIDTH, HEIGHT = 860, 56
FONT_SIZE = 20
BASELINE = 36
SIDE_MARGIN = 20
SECONDS_PER_CHAR = 0.06
START_DELAY = 0.3


def render_tagline(prompt_user: str, tagline: str) -> str:
    cw = char_width(FONT_SIZE)
    prompt = f"{prompt_user} ~ $ "
    typed = f'echo "{tagline}"'
    require_fit("prompt", prompt, FONT_SIZE, (WIDTH - 2 * SIDE_MARGIN) / 2)
    total_w = (len(prompt) + len(typed)) * cw
    if total_w > WIDTH - 2 * SIDE_MARGIN:
        max_chars = int((WIDTH - 2 * SIDE_MARGIN) // cw) - len(prompt) - len('echo ""')
        raise ValueError(f"tagline is {len(tagline)} characters; max is {max_chars} to fit {WIDTH}px")
    typed_w = len(typed) * cw
    x0 = (WIDTH - total_w) / 2
    x_typed = x0 + len(prompt) * cw
    x_end = x_typed + typed_w
    duration = len(typed) * SECONDS_PER_CHAR
    steps = f"{duration:.2f}s steps({len(typed)}, end) {START_DELAY}s both"
    css = (
        f"@keyframes type {{ from {{ transform: translateX(-{typed_w:.1f}px); }} }}\n"
        "@keyframes blink { 50% { opacity: 0; } }\n"
        f".typing {{ animation: type {steps}; }}\n"
        f".cursor {{ animation: type {steps}, blink 1s step-end {START_DELAY + duration:.2f}s infinite; }}"
    )
    body = (
        f'<rect width="{WIDTH}" height="{HEIGHT}" rx="8" fill="{BG}"/>'
        f'<text x="{x0:.1f}" y="{BASELINE}" font-size="{FONT_SIZE}" textLength="{len(prompt) * cw:.1f}" '
        f'xml:space="preserve"><tspan fill="{PROMPT}">{esc(prompt_user)}</tspan>'
        f'<tspan fill="{PATH_BLUE}"> ~</tspan><tspan fill="{TEXT}"> $ </tspan></text>'
        f'<text x="{x_typed:.1f}" y="{BASELINE}" font-size="{FONT_SIZE}" fill="{TEXT}" '
        f'textLength="{typed_w:.1f}" xml:space="preserve">{esc(typed)}</text>'
        f'<rect class="typing" x="{x_end:.1f}" y="10" width="{typed_w + cw:.1f}" height="36" fill="{BG}"/>'
        f'<rect class="cursor" x="{x_end:.1f}" y="{BASELINE - FONT_SIZE + 3}" width="{cw:.1f}" '
        f'height="{FONT_SIZE + 2}" fill="{TEXT}"/>'
        # border last so the resting cover rect never hides it
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="8" fill="none" stroke="{BORDER}"/>'
    )
    return svg_doc(WIDTH, HEIGHT, body, css)


def main() -> None:
    profile = load_profile()
    write_svg(ASSETS / "tagline.svg", render_tagline(profile["prompt"], profile["tagline"]))


if __name__ == "__main__":
    main()
