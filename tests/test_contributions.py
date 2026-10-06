from datetime import date, timedelta
from pathlib import Path

import pytest
import requests

import fetch_contributions as fc
from fetch_contributions import CalendarError, Day

FIXTURE = Path(__file__).parent / "fixtures" / "contributions.html"


def make_days(counts, start=date(2026, 1, 1)):
    return [Day(start + timedelta(days=i), c, min(c, 4)) for i, c in enumerate(counts)]


def test_parses_fixture():
    days = fc.parse_calendar(FIXTURE.read_text(encoding="utf-8"))
    assert len(days) == 367
    assert days[0].day == date(2025, 10, 5) and days[-1].day == date(2026, 10, 6)
    assert sum(d.count for d in days) == 1045
    assert Day(date(2026, 10, 3), 145, 4) in days
    fc.validate_days(days)


@pytest.mark.parametrize(
    "text, expected",
    [("No contributions on May 1st.", 0), ("1 contribution on May 1st.", 1), ("1,234 contributions on May 1st.", 1234)],
)
def test_parse_count(text, expected):
    assert fc.parse_count(text) == expected


def test_unknown_tooltip_wording_raises():
    with pytest.raises(CalendarError, match="unrecognized"):
        fc.parse_count("Five commits that day")


def test_cell_without_tooltip_raises():
    html = '<table><td class="ContributionCalendar-day" data-date="2026-01-01" id="x" data-level="0"></td></table>'
    with pytest.raises(CalendarError, match="no tooltip"):
        fc.parse_calendar(html)


@pytest.mark.parametrize(
    "days, message",
    [
        (make_days([1] * 10), "at least"),
        (make_days([1] * 200) + make_days([1] * 200, start=date(2026, 7, 21)), "contiguous"),
        (make_days([1] * 360) + [Day(date(2026, 1, 1) + timedelta(days=359), 1, 1)], "contiguous"),
        (make_days([1] * 359) + [Day(date(2026, 1, 1) + timedelta(days=359), 9, 5)], "out-of-range"),
    ],
)
def test_validation_failures(days, message):
    with pytest.raises(CalendarError, match=message):
        fc.validate_days(days)


@pytest.mark.parametrize(
    "counts, current, longest",
    [
        ([0, 0, 0], 0, 0),
        ([1, 1, 0, 1, 1, 1], 3, 3),
        ([1, 1, 1, 0], 3, 3),  # today still zero: streak runs through yesterday
        ([1, 0, 0], 0, 1),
        ([2, 2, 2, 2, 0, 1], 1, 4),
    ],
)
def test_streaks(counts, current, longest):
    days = make_days(counts)
    assert fc.current_streak(days) == current
    assert fc.longest_streak(days) == longest


def test_best_day_prefers_most_recent_tie_and_none_when_empty():
    assert fc.best_day(make_days([5, 1, 5, 0])).day == date(2026, 1, 3)
    assert fc.best_day(make_days([0, 0])) is None


def test_zero_year_summary():
    summary = fc.build_summary(make_days([0] * 3))
    assert summary["stats"] == {"total": 0, "current_streak": 0, "longest_streak": 0, "best_day": None}
    assert summary["days"][0] == {"date": "2026-01-01", "count": 0, "level": 0}


def test_network_failure_returns_1_and_writes_nothing(monkeypatch, tmp_path):
    target = tmp_path / "contributions.json"
    monkeypatch.setattr(fc, "DATA_PATH", target)

    def offline(user):
        raise requests.ConnectionError("offline")

    monkeypatch.setattr(fc, "fetch_html", offline)
    assert fc.main() == 1
    assert not target.exists()


def test_main_writes_summary(monkeypatch, tmp_path):
    target = tmp_path / "contributions.json"
    monkeypatch.setattr(fc, "DATA_PATH", target)
    monkeypatch.setattr(fc, "fetch_html", lambda user: FIXTURE.read_text(encoding="utf-8"))
    assert fc.main() == 0
    assert '"total": 1045' in target.read_text(encoding="utf-8")
