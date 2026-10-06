import re
from datetime import date, timedelta
from pathlib import Path

import pytest

import fetch_contributions as fc
import render_heatmap_svg as rh

FIXTURE = Path(__file__).parent / "fixtures" / "contributions.html"


@pytest.fixture
def summary():
    return fc.build_summary(fc.parse_calendar(FIXTURE.read_text(encoding="utf-8")))


def synthetic(start: date, n: int, count: int = 0) -> dict:
    return fc.build_summary([fc.Day(start + timedelta(days=i), count, min(count, 4)) for i in range(n)])


def test_fixture_renders_one_cell_per_day(check_svg, summary):
    svg = rh.render_heatmap(summary)
    check_svg(svg, rh.WIDTH)
    assert svg.count('class="c"') == len(summary["days"])
    assert "1,045 contributions in the last year" in svg


def test_grid_fits_inside_width(summary):
    xs = [float(x) for x in re.findall(r'class="c" x="([\d.]+)"', rh.render_heatmap(summary))]
    assert min(xs) >= rh.LABEL_W and max(xs) + rh.CELL <= rh.WIDTH


def test_mid_week_start_lands_on_correct_row():
    placed = rh.place(synthetic(date(2026, 1, 7), 400)["days"])  # a Wednesday
    assert placed[0][:2] == (0, 3)
    assert placed[4][:2] == (1, 0)  # the following Sunday starts column 1


def test_month_labels_never_crowd(summary):
    cols = [col for col, _ in rh.month_labels(rh.place(summary["days"]))]
    assert all(b - a >= 3 for a, b in zip(cols, cols[1:]))


def test_zero_year_footer():
    line1, line2 = rh.footer_lines(synthetic(date(2026, 1, 4), 365)["stats"])
    assert line1 == "0 contributions in the last year"
    assert "best day" not in line2


def test_footer_singular_and_best_day():
    stats = {"total": 1, "current_streak": 1, "longest_streak": 1, "best_day": {"date": "2026-10-03", "count": 145}}
    line1, line2 = rh.footer_lines(stats)
    assert line1 == "1 contribution in the last year"
    assert line2 == "current streak 1 day · longest 1 day · best day 145 on Oct 3"


def test_malformed_summary_raises():
    with pytest.raises(ValueError, match="days"):
        rh.render_heatmap({"stats": {}})
