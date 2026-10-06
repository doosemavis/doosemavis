import pytest

from make_project_cards import WIDTH, render_project_card
from svg_common import DIM, LANG_COLORS


def test_every_repo_project_renders(check_svg, profile):
    for project in profile["projects"]:
        svg = render_project_card(project)
        check_svg(svg, WIDTH)
        assert f"~/projects/{project['name']}" in svg
        assert LANG_COLORS[project["lang"]] in svg


def test_unknown_language_falls_back_to_dim(profile):
    project = {**profile["projects"][0], "lang": "Zig"}
    assert f'r="5" fill="{DIM}"/><text' in render_project_card(project)


def test_blurb_that_needs_four_lines_raises(profile):
    project = {**profile["projects"][0], "blurb": "word " * 40}
    with pytest.raises(ValueError, match="blurb"):
        render_project_card(project)


def test_escapes_blurb(check_svg, profile):
    svg = render_project_card({**profile["projects"][0], "blurb": "fast & <small>"})
    check_svg(svg)
    assert "fast &amp; &lt;small&gt;" in svg
