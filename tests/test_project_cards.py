import pytest

from make_project_cards import WIDTH, render_project_card
from svg_common import DIM, LANG_COLORS

SAMPLE = {"slug": "demo", "name": "demo", "repo": "me/demo", "blurb": "A demo project.", "lang": "TypeScript"}


def test_every_real_project_renders(check_svg, profile):
    for project in profile["projects"]:
        check_svg(render_project_card(project), WIDTH)


def test_card_shows_path_title_and_language_color(check_svg):
    svg = render_project_card(SAMPLE)
    check_svg(svg, WIDTH)
    assert "~/projects/demo" in svg
    assert LANG_COLORS["TypeScript"] in svg


def test_unknown_language_falls_back_to_dim():
    assert f'r="5" fill="{DIM}"/><text' in render_project_card({**SAMPLE, "lang": "Zig"})


def test_blurb_that_needs_four_lines_raises():
    with pytest.raises(ValueError, match="blurb"):
        render_project_card({**SAMPLE, "blurb": "word " * 40})


def test_escapes_blurb(check_svg):
    svg = render_project_card({**SAMPLE, "blurb": "fast & <small>"})
    check_svg(svg)
    assert "fast &amp; &lt;small&gt;" in svg


def test_name_too_wide_for_card_raises():
    with pytest.raises(ValueError, match="project name"):
        render_project_card({**SAMPLE, "name": "n" * 30})
