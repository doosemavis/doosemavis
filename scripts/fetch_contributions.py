"""Fetch the public contribution calendar and write data/contributions.json (no token needed)."""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from svg_common import ROOT

DATA_PATH = ROOT / "data" / "contributions.json"
URL = "https://github.com/users/{user}/contributions"
USER_AGENT = "Mozilla/5.0 (profile-art; +https://github.com/doosemavis/doosemavis)"
TIMEOUT_S = 20
MIN_DAYS = 350
MAX_LEVEL = 4
COUNT_RE = re.compile(r"^([\d,]+) contributions? on ")


class CalendarError(ValueError):
    """The calendar HTML could not be parsed or failed validation."""


@dataclass(frozen=True)
class Day:
    day: date
    count: int
    level: int


def parse_count(tooltip: str) -> int:
    if tooltip.startswith("No contributions"):
        return 0
    match = COUNT_RE.match(tooltip)
    if not match:
        raise CalendarError(f"unrecognized tooltip text: {tooltip!r}")
    return int(match.group(1).replace(",", ""))


def parse_calendar(html: str) -> list[Day]:
    soup = BeautifulSoup(html, "html.parser")
    tooltips = {tip.get("for"): tip.get_text(strip=True) for tip in soup.find_all("tool-tip")}
    days = []
    for cell in soup.select("td.ContributionCalendar-day[data-date]"):
        tooltip = tooltips.get(cell.get("id"))
        if tooltip is None:
            raise CalendarError(f"no tooltip for day {cell['data-date']}")
        try:
            day, level = date.fromisoformat(cell["data-date"]), int(cell.get("data-level", ""))
        except ValueError as err:
            raise CalendarError(f"bad day cell {cell.get('data-date')!r}: {err}") from err
        days.append(Day(day, parse_count(tooltip), level))
    return sorted(days, key=lambda d: d.day)


def validate_days(days: list[Day]) -> None:
    if len(days) < MIN_DAYS:
        raise CalendarError(f"expected at least {MIN_DAYS} days, parsed {len(days)}")
    for prev, cur in zip(days, days[1:]):
        if cur.day - prev.day != timedelta(days=1):
            raise CalendarError(f"calendar not contiguous between {prev.day} and {cur.day}")
    bad = next((d for d in days if not 0 <= d.level <= MAX_LEVEL or d.count < 0), None)
    if bad:
        raise CalendarError(f"out-of-range level or count on {bad.day}")


def longest_streak(days: list[Day]) -> int:
    best = run = 0
    for d in days:
        run = run + 1 if d.count > 0 else 0
        best = max(best, run)
    return best


def current_streak(days: list[Day]) -> int:
    # today may just not have activity yet, so a zero on the last day doesn't break the streak
    tail = days[:-1] if days and days[-1].count == 0 else days
    run = 0
    for d in reversed(tail):
        if d.count == 0:
            break
        run += 1
    return run


def best_day(days: list[Day]) -> Day | None:
    top = max(days, key=lambda d: (d.count, d.day), default=None)
    return top if top and top.count > 0 else None


def build_summary(days: list[Day]) -> dict:
    top = best_day(days)
    return {
        "days": [{"date": d.day.isoformat(), "count": d.count, "level": d.level} for d in days],
        "stats": {
            "total": sum(d.count for d in days),
            "current_streak": current_streak(days),
            "longest_streak": longest_streak(days),
            "best_day": {"date": top.day.isoformat(), "count": top.count} if top else None,
        },
    }


def fetch_html(user: str) -> str:
    response = requests.get(URL.format(user=user), headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_S)
    response.raise_for_status()
    return response.text


def write_json_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    tmp.replace(path)


def main() -> int:
    user = os.environ.get("PROFILE_USER", "doosemavis")
    try:
        days = parse_calendar(fetch_html(user))
        validate_days(days)
    except (requests.RequestException, CalendarError) as err:
        print(f"fetch_contributions: {err}", file=sys.stderr)
        return 1
    write_json_atomic(DATA_PATH, build_summary(days))
    print(f"fetch_contributions: wrote {len(days)} days to {DATA_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
