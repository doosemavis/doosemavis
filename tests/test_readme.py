import re
from pathlib import Path

README = Path(__file__).resolve().parent.parent / "README.md"
PROFILE_COLUMN_PX = 830  # GitHub's profile README column on desktop
CELL_OVERHEAD_PX = 2 * 13 + 1  # GitHub table cell padding plus one border
ROW_RE = re.compile(r"<tr>(.*?)</tr>", re.S)
WIDTH_RE = re.compile(r'<img[^>]*width="(\d+)"')


def test_table_rows_fit_the_profile_column():
    rows = ROW_RE.findall(README.read_text(encoding="utf-8"))
    assert rows, "README should lay images out in table rows"
    for row in rows:
        widths = [int(w) for w in WIDTH_RE.findall(row)]
        row_px = sum(widths) + len(widths) * CELL_OVERHEAD_PX + 1
        assert row_px <= PROFILE_COLUMN_PX, f"row of {widths} renders ~{row_px}px"
