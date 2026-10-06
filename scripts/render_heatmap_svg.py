"""Render data/contributions.json as an animated contribution heatmap: assets/contrib-heatmap.svg."""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta

from svg_common import ASSETS, BG, BORDER, DIM, HEAT_LEVELS, ROOT, TEXT, esc, svg_doc, write_svg

DATA_PATH = ROOT / "data" / "contributions.json"
WIDTH = 860
CELL, GAP = 12, 3
STEP = CELL + GAP
LABEL_W = 30
GRID_TOP = 34
FONT_SIZE = 11
DELAY_PER_DIAGONAL = 0.035
MIN_LABEL_GAP_COLS = 3
WEEKDAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
CSS = (
    "@keyframes pop { from { opacity: 0; transform: translateY(-4px); } }\n"
    ".c { animation: pop .4s ease-out both; }"
)


def _sunday_row(d: date) -> int:
    return (d.weekday() + 1) % 7


def place(days: list[dict]) -> list[tuple[int, int, dict]]:
    """(column, row, day) per day; columns are Sunday-first weeks like GitHub's calendar."""
    first = date.fromisoformat(days[0]["date"])
    origin = first - timedelta(days=_sunday_row(first))
    placed = []
    for day in days:
        d = date.fromisoformat(day["date"])
        placed.append(((d - origin).days // 7, _sunday_row(d), day))
    return placed


def month_labels(placed: list[tuple[int, int, dict]]) -> list[tuple[int, str]]:
    first_in_col: dict[int, date] = {}
    for col, _, day in placed:
        first_in_col.setdefault(col, date.fromisoformat(day["date"]))
    labels, prev_month = [], None
    for col in sorted(first_in_col):
        month = first_in_col[col].month
        if month != prev_month:
            labels.append((col, MONTHS[month - 1]))
            prev_month = month
    if len(labels) > 1 and labels[1][0] - labels[0][0] < MIN_LABEL_GAP_COLS:
        labels.pop(0)
    return labels


def _plural(n: int, word: str) -> str:
    return f"{n:,} {word}{'' if n == 1 else 's'}"


def footer_lines(stats: dict) -> tuple[str, str]:
    line1 = f"{_plural(stats['total'], 'contribution')} in the last year"
    parts = [
        f"current streak {_plural(stats['current_streak'], 'day')}",
        f"longest {_plural(stats['longest_streak'], 'day')}",
    ]
    best = stats.get("best_day")
    if best:
        d = date.fromisoformat(best["date"])
        parts.append(f"best day {best['count']:,} on {MONTHS[d.month - 1]} {d.day}")
    return line1, " · ".join(parts)


def _label(x: float, y: float, text: str, fill: str = DIM, anchor: str = "start") -> str:
    return f'<text x="{x:.1f}" y="{y}" font-size="{FONT_SIZE}" fill="{fill}" text-anchor="{anchor}">{esc(text)}</text>'


def _legend(right: float, y: float) -> list[str]:
    squares_x = right - 32 - (len(HEAT_LEVELS) * STEP - GAP)
    squares = [
        f'<rect x="{squares_x + i * STEP:.1f}" y="{y - CELL + 2}" width="{CELL}" height="{CELL}" rx="2" fill="{color}"/>'
        for i, color in enumerate(HEAT_LEVELS)
    ]
    return [_label(squares_x - 6, y, "Less", anchor="end"), *squares, _label(right, y, "More", anchor="end")]


def render_heatmap(summary: dict) -> str:
    days, stats = summary.get("days"), summary.get("stats")
    if not days or not isinstance(stats, dict):
        raise ValueError("summary needs non-empty 'days' and a 'stats' object")
    placed = place(days)
    grid_w = (placed[-1][0] + 1) * STEP - GAP
    x0 = LABEL_W + (WIDTH - LABEL_W - grid_w) / 2
    y1 = GRID_TOP + 7 * STEP - GAP + 26
    y2 = y1 + 20
    height = y2 + 16
    line1, line2 = footer_lines(stats)
    parts = [f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="8" fill="{BG}" stroke="{BORDER}"/>']
    parts += [_label(x0 + col * STEP, GRID_TOP - 8, name) for col, name in month_labels(placed)]
    parts += [_label(x0 - 6, GRID_TOP + row * STEP + CELL - 2, name, anchor="end") for row, name in WEEKDAY_LABELS.items()]
    parts += [
        f'<rect class="c" x="{x0 + col * STEP:.1f}" y="{GRID_TOP + row * STEP}" width="{CELL}" height="{CELL}" '
        f'rx="2" fill="{HEAT_LEVELS[day["level"]]}" style="animation-delay:{(col + row) * DELAY_PER_DIAGONAL:.3f}s"/>'
        for col, row, day in placed
    ]
    parts += [_label(x0, y1, line1, fill=TEXT), _label(x0, y2, line2), *_legend(x0 + grid_w, y1)]
    return svg_doc(WIDTH, height, "".join(parts), CSS)


def main() -> int:
    try:
        svg = render_heatmap(json.loads(DATA_PATH.read_text(encoding="utf-8")))
    except (OSError, ValueError) as err:
        print(f"render_heatmap_svg: {err}", file=sys.stderr)
        return 1
    write_svg(ASSETS / "contrib-heatmap.svg", svg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
