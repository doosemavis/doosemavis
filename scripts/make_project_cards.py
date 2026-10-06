"""Render one terminal-window card per featured project: assets/project-<slug>.svg."""
from __future__ import annotations

from profile_data import load_profile
from svg_common import (ASSETS, DIM, LANG_COLORS, TEXT, char_width, esc, require_fit, svg_doc,
                        window_frame, wrap, write_svg)

WIDTH = 280
PAD_X = 16
NAME_SIZE = 15
NAME_BASELINE = 56
BLURB_SIZE = 12
BLURB_BASELINE = 80
BLURB_LINE_HEIGHT = 17
MAX_BLURB_LINES = 3
LANG_SIZE = 11


def render_project_card(project: dict) -> str:
    require_fit("project name", project["name"], NAME_SIZE, WIDTH - 2 * PAD_X)
    blurb_chars = int((WIDTH - 2 * PAD_X) // char_width(BLURB_SIZE))
    lines = wrap(project["blurb"], blurb_chars)
    if len(lines) > MAX_BLURB_LINES:
        raise ValueError(
            f"blurb for {project['slug']!r} wraps to {len(lines)} lines; "
            f"max is {MAX_BLURB_LINES} (about {blurb_chars * MAX_BLURB_LINES} characters)"
        )
    lang_y = BLURB_BASELINE + MAX_BLURB_LINES * BLURB_LINE_HEIGHT + 8
    height = lang_y + 18
    blurb = "".join(
        f'<text x="{PAD_X}" y="{BLURB_BASELINE + i * BLURB_LINE_HEIGHT}" font-size="{BLURB_SIZE}" '
        f'fill="{DIM}">{esc(line)}</text>'
        for i, line in enumerate(lines)
    )
    lang_color = LANG_COLORS.get(project["lang"], DIM)
    body = (
        window_frame(WIDTH, height, f"~/projects/{project['name']}")
        + f'<text x="{PAD_X}" y="{NAME_BASELINE}" font-size="{NAME_SIZE}" font-weight="bold" '
        f'fill="{TEXT}">{esc(project["name"])}</text>'
        + blurb
        + f'<circle cx="{PAD_X + 5}" cy="{lang_y - 4}" r="5" fill="{lang_color}"/>'
        f'<text x="{PAD_X + 16}" y="{lang_y}" font-size="{LANG_SIZE}" fill="{DIM}">{esc(project["lang"])}</text>'
    )
    return svg_doc(WIDTH, height, body)


def main() -> None:
    for project in load_profile()["projects"]:
        write_svg(ASSETS / f"project-{project['slug']}.svg", render_project_card(project))


if __name__ == "__main__":
    main()
