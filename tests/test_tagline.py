import re

import pytest

from make_tagline import HEIGHT, WIDTH, render_tagline

TYPED_RE = re.compile(r'<text x="([\d.]+)"[^>]*fill="#c9d1d9" textLength="([\d.]+)"')


def test_renders_valid_svg_with_escaped_text(check_svg):
    svg = render_tagline("moose@github", "ship & <learn>")
    check_svg(svg, WIDTH, HEIGHT)
    assert "echo &quot;ship &amp; &lt;learn&gt;&quot;" in svg


def test_only_the_cursor_loops():
    assert render_tagline("moose@github", "building things that ship").count("infinite") == 1


def test_cover_rests_after_the_text_so_static_frame_shows_everything():
    svg = render_tagline("moose@github", "hi")
    text_x, text_w = (float(v) for v in TYPED_RE.search(svg).groups())
    cover_x = float(re.search(r'<rect class="typing" x="([\d.]+)"', svg).group(1))
    assert cover_x >= text_x + text_w - 0.1


def test_too_long_tagline_raises():
    with pytest.raises(ValueError, match="tagline"):
        render_tagline("moose@github", "x" * 60)
