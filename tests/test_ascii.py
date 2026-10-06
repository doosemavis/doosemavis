import re

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("PIL")

from make_ascii_svg import PAD, RAMP, render_ascii, to_grid  # noqa: E402


def test_dark_is_blank_and_bright_is_dense():
    gradient = np.tile(np.linspace(0, 255, 13).astype(np.uint8), (13, 1))
    row = to_grid(gradient, cols=13)[0]
    assert row[0] == " " and row[-1] == "@"
    indexes = [RAMP.index(ch) for ch in row]
    assert indexes == sorted(indexes)


def test_grid_shape_uses_glyph_aspect():
    rows = to_grid(np.zeros((100, 200), dtype=np.uint8), cols=40)
    assert len(rows) == 12 and all(len(r) == 40 for r in rows)


def test_rows_share_text_length_and_covers_rest_past_the_text(check_svg):
    svg = render_ascii(["@@  ", " %% ", "  ##"])
    check_svg(svg)
    lengths = re.findall(r'textLength="([\d.]+)"', svg)
    assert len(lengths) == 3 and len(set(lengths)) == 1
    cover_xs = [float(x) for x in re.findall(r'class="w" x="([\d.]+)"', svg)]
    assert cover_xs and all(x >= PAD + float(lengths[0]) - 0.1 for x in cover_xs)
