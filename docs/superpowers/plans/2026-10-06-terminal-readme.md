# Terminal-style Profile README Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the doosemavis profile README with a terminal-themed page built entirely from committed, self-generated animated SVGs, with the contribution heatmap refreshed daily by GitHub Actions.

**Architecture:** One small Python CLI per SVG in `scripts/`, each a pure `render_*()` function plus a thin `main()`. Text comes from `profile.json`; contribution data from GitHub's public calendar HTML into `data/contributions.json`. The README only places the SVGs. All animation is CSS keyframes inside each SVG whose resting (non-animated) state is the final frame.

**Tech Stack:** Python 3.11, requests, beautifulsoup4, pytest; local-only portrait: Pillow, numpy, opencv-python-headless, rembg; GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-06-terminal-readme-design.md`

## Global Constraints

- Python 3.11 locally (`python3.11 -m venv .venv`) and in CI (`python-version: "3.11"`).
- CI installs only `scripts/requirements.txt`: `requests==2.32.3`, `beautifulsoup4==4.12.3`, `pytest==8.3.3`.
- Colors only from `scripts/svg_common.py`: bg `#0d1117`, panel `#161b22`, border `#30363d`, text `#c9d1d9`, dim `#8b949e`, prompt `#3fb950`; heat levels `#161b22 #0e4429 #006d32 #26a641 #39d353`; keys `#ff7b72 #3fb950 #d29922 #58a6ff #bc8cff #39c5cf`.
- Font stack: `ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace`.
- Widths: tagline 860, heatmap 860, portrait displayed 370, info card 490, project cards 280.
- CSS keyframes only, never SMIL (`<animate`). Every SVG includes the reduced-motion rule; the un-animated state is the final frame. Only the tagline cursor loops.
- No employer names anywhere. The source photo and `.portrait/` never get committed.
- Commit messages: conventional commits, ending with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. GitHub changes the contributions HTML (new tooltip wording, missing attributes) → the fetch fails loudly with a clear message and writes nothing, so yesterday's heatmap stays live. (Task 5 tests: unknown tooltip, missing tooltip, network error leaves no file.)
2. Someone edits `profile.json` with text that's too long → generators wrap where they can and otherwise stop with an error naming the field and limit, never render overflowing text. (Tasks 2–4 tests.)
3. A viewer has reduced motion on, or the renderer skips CSS animation → they see the finished art, not a blank or half-typed frame. (Tests assert the reduced-motion rule, no SMIL, and that cover rects rest beyond the text.)
4. The calendar window starts mid-week or ends on a partial week → days land on the correct weekday row and the grid still fits 860px. (Task 6 tests.)
5. A year with zero contributions → footer reads "0 contributions in the last year", omits best day, no crash. (Tasks 5–6 tests.)

---

### Task 1: Scaffold, shared SVG helpers, profile loader

**Files:**
- Create: `.gitignore`, `pytest.ini`, `profile.json`, `scripts/requirements.txt`, `scripts/requirements-portrait.txt`, `scripts/svg_common.py`, `scripts/profile_data.py`, `tests/conftest.py`, `tests/test_svg_common.py`, `tests/test_profile_data.py`
- Already present: `tests/fixtures/contributions.html` (saved 2026-10-06; 367 days, 2025-10-05 → 2026-10-06, total 1,045)

**Interfaces:**
- Produces: `svg_common` constants listed in Global Constraints plus `PATH_BLUE`, `WINDOW_DOTS`, `LANG_COLORS`, `ROOT`, `ASSETS`, `REDUCED_MOTION`; functions `esc(str)->str`, `char_width(font_size)->float`, `wrap(text, width)->list[str]`, `svg_doc(width, height, body, css="")->str`, `window_frame(width, height, title)->str`, `write_svg(path, svg)->None`.
- Produces: `profile_data.load_profile(path=PROFILE_PATH)->dict`, `validate_profile(dict)->None`, `ProfileError(ValueError)`.
- Produces: pytest fixtures `check_svg(svg, width=None, height=None)->Element`, `profile()->dict`.

- [ ] **Step 1: Scaffold files**

`.gitignore`
```
.venv/
__pycache__/
.pytest_cache/
.portrait/
*.tmp
*.jpg
*.jpeg
*.JPG
*.JPEG
*.png
*.PNG
*.heic
*.HEIC
```

`pytest.ini`
```ini
[pytest]
pythonpath = scripts
testpaths = tests
```

`scripts/requirements.txt`
```
requests==2.32.3
beautifulsoup4==4.12.3
pytest==8.3.3
```

`scripts/requirements-portrait.txt`
```
-r requirements.txt
pillow
numpy
opencv-python-headless
rembg[cpu]
```

`profile.json`: exactly the JSON block in the spec's "Content" section.

Run: `python3.11 -m venv .venv && .venv/bin/pip install -q -r scripts/requirements.txt`

- [ ] **Step 2: Write failing tests**

`tests/conftest.py`
```python
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from svg_common import REDUCED_MOTION

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def check_svg():
    """Parse an SVG string and assert the rules every generated SVG must follow."""

    def _check(svg: str, width: int | None = None, height: int | None = None) -> ET.Element:
        root = ET.fromstring(svg)
        assert REDUCED_MOTION in svg
        assert "<animate" not in svg, "use CSS keyframes, not SMIL"
        if width is not None:
            assert root.get("width") == str(width)
        if height is not None:
            assert root.get("height") == str(height)
        return root

    return _check


@pytest.fixture
def profile() -> dict:
    return json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))
```

`tests/test_svg_common.py`
```python
import svg_common as sc


def test_esc_escapes_markup_and_quotes():
    assert sc.esc('a & <b> "c"') == "a &amp; &lt;b&gt; &quot;c&quot;"


def test_svg_doc_has_viewbox_font_and_reduced_motion(check_svg):
    root = check_svg(sc.svg_doc(100, 50, '<rect width="1" height="1"/>'), 100, 50)
    assert root.get("viewBox") == "0 0 100 50"


def test_window_frame_escapes_title(check_svg):
    svg = sc.svg_doc(200, 100, sc.window_frame(200, 100, "a & b"))
    check_svg(svg)
    assert "a &amp; b" in svg


def test_wrap_never_exceeds_width():
    assert all(len(line) <= 10 for line in sc.wrap("one two three four five six", 10))


def test_char_width_is_point_six_em():
    assert sc.char_width(20) == 12
```

`tests/test_profile_data.py`
```python
import pytest

from profile_data import ProfileError, load_profile, validate_profile


def test_repo_profile_is_valid():
    data = load_profile()
    assert data["prompt"] == "moose@github"


def test_invalid_json_raises(tmp_path):
    bad = tmp_path / "profile.json"
    bad.write_text("{nope", encoding="utf-8")
    with pytest.raises(ProfileError, match="not valid JSON"):
        load_profile(bad)


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda p: p.pop("tagline"), "tagline"),
        (lambda p: p["card"].append(["only-key"]), "card rows"),
        (lambda p: p["projects"][0].update(slug="Bad Slug"), "slug"),
        (lambda p: p["projects"][0].update(blurb=""), "blurb"),
        (lambda p: p.update(projects=["not-a-dict"]), "projects"),
    ],
)
def test_validation_names_the_problem(profile, mutate, message):
    mutate(profile)
    with pytest.raises(ProfileError, match=message):
        validate_profile(profile)
```

- [ ] **Step 3: Run tests, expect FAIL**: `.venv/bin/pytest -q` → `ModuleNotFoundError: No module named 'svg_common'`.

- [ ] **Step 4: Implement**

`scripts/svg_common.py`
```python
"""Palette, font stack and SVG helpers shared by every profile-art generator."""
from __future__ import annotations

import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

BG = "#0d1117"
PANEL = "#161b22"
BORDER = "#30363d"
TEXT = "#c9d1d9"
DIM = "#8b949e"
PROMPT = "#3fb950"
PATH_BLUE = "#58a6ff"
HEAT_LEVELS = ("#161b22", "#0e4429", "#006d32", "#26a641", "#39d353")
KEY_COLORS = ("#ff7b72", "#3fb950", "#d29922", "#58a6ff", "#bc8cff", "#39c5cf")
WINDOW_DOTS = ("#ff5f57", "#febc2e", "#28c840")
LANG_COLORS = {"TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Python": "#3572a5", "Ruby": "#701516"}

FONT_STACK = 'ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace'
CHAR_WIDTH_EM = 0.6  # advance width of one monospace glyph
REDUCED_MOTION = "@media (prefers-reduced-motion: reduce) { * { animation: none !important; } }"


def esc(text: str) -> str:
    """Escape text for SVG element content or attribute values."""
    return escape(text, {'"': "&quot;"})


def char_width(font_size: float) -> float:
    return font_size * CHAR_WIDTH_EM


def wrap(text: str, width: int) -> list[str]:
    return textwrap.wrap(text, width=width, break_long_words=True)


def svg_doc(width: int, height: int, body: str, css: str = "") -> str:
    """Standalone SVG with the shared font and the reduced-motion rule."""
    style = f"text {{ font-family: {FONT_STACK}; }}\n{css}\n{REDUCED_MOTION}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n<style>\n{style}\n</style>\n{body}\n</svg>\n'
    )


def window_frame(width: int, height: int, title: str) -> str:
    """Dark rounded window with a title bar, traffic-light dots and a border."""
    dots = "".join(
        f'<circle cx="{16 + i * 16}" cy="14" r="5" fill="{color}"/>' for i, color in enumerate(WINDOW_DOTS)
    )
    return (
        f'<rect width="{width}" height="{height}" rx="8" fill="{BG}"/>'
        f'<rect width="{width}" height="28" rx="8" fill="{PANEL}"/>'
        f'<rect y="20" width="{width}" height="8" fill="{PANEL}"/>'
        f'<line x1="0" y1="28" x2="{width}" y2="28" stroke="{BORDER}"/>'
        f"{dots}"
        f'<text x="72" y="18" font-size="11" fill="{DIM}">{esc(title)}</text>'
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="8" fill="none" stroke="{BORDER}"/>'
    )


def write_svg(path: Path, svg: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")
```

`scripts/profile_data.py`
```python
"""Load and validate profile.json, the single source of text for the profile art."""
from __future__ import annotations

import json
import re
from pathlib import Path

from svg_common import ROOT

PROFILE_PATH = ROOT / "profile.json"
SLUG_RE = re.compile(r"^[a-z0-9-]+$")
PROJECT_KEYS = ("slug", "name", "repo", "blurb", "lang")


class ProfileError(ValueError):
    """profile.json is missing fields or has the wrong shape."""


def load_profile(path: Path = PROFILE_PATH) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        raise ProfileError(f"{path} is not valid JSON: {err}") from err
    validate_profile(data)
    return data


def _non_empty_str(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_profile(data: dict) -> None:
    for key in ("prompt", "tagline"):
        if not _non_empty_str(data.get(key)):
            raise ProfileError(f"profile.json needs a non-empty string {key!r}")
    card = data.get("card")
    if not isinstance(card, list) or not card:
        raise ProfileError("profile.json needs a non-empty 'card' list")
    for row in card:
        if not (isinstance(row, list) and len(row) == 2 and all(_non_empty_str(s) for s in row)):
            raise ProfileError(f"card rows must be [key, value] string pairs, got {row!r}")
    projects = data.get("projects")
    if not isinstance(projects, list) or not projects:
        raise ProfileError("profile.json needs a non-empty 'projects' list")
    for project in projects:
        if not isinstance(project, dict):
            raise ProfileError(f"projects entries must be objects, got {project!r}")
        for key in PROJECT_KEYS:
            if not _non_empty_str(project.get(key)):
                raise ProfileError(f"project {project.get('slug', '?')!r} needs a non-empty {key!r}")
        if not SLUG_RE.match(project["slug"]):
            raise ProfileError(f"project slug {project['slug']!r} must be lowercase letters, digits or '-'")
```

- [ ] **Step 5: Run tests, expect PASS**: `.venv/bin/pytest -q`
- [ ] **Step 6: Commit**: `feat: scaffold profile-art scripts with shared SVG helpers and profile loader`

---

### Task 2: Typing tagline

**Files:** Create `scripts/make_tagline.py`, `tests/test_tagline.py`

**Interfaces:**
- Consumes: `load_profile`, `svg_common.{ASSETS, BG, BORDER, PATH_BLUE, PROMPT, TEXT, char_width, esc, svg_doc, write_svg}`
- Produces: `render_tagline(prompt_user: str, tagline: str) -> str`; writes `assets/tagline.svg` (860×56).

- [ ] **Step 1: Write failing tests**: `tests/test_tagline.py`
```python
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
```

- [ ] **Step 2: Run, expect FAIL**: `.venv/bin/pytest tests/test_tagline.py -q` → `ModuleNotFoundError: make_tagline`.

- [ ] **Step 3: Implement**: `scripts/make_tagline.py`
```python
"""Render assets/tagline.svg: a prompt that types `echo "<tagline>"` once, then blinks a cursor."""
from __future__ import annotations

from profile_data import load_profile
from svg_common import ASSETS, BG, BORDER, PATH_BLUE, PROMPT, TEXT, char_width, esc, svg_doc, write_svg

WIDTH, HEIGHT = 860, 56
FONT_SIZE = 20
BASELINE = 36
SIDE_MARGIN = 20
SECONDS_PER_CHAR = 0.06
START_DELAY = 0.3


def render_tagline(prompt_user: str, tagline: str) -> str:
    cw = char_width(FONT_SIZE)
    prompt = f"{prompt_user} ~ $ "
    typed = f'echo "{tagline}"'
    total_w = (len(prompt) + len(typed)) * cw
    if total_w > WIDTH - 2 * SIDE_MARGIN:
        max_chars = int((WIDTH - 2 * SIDE_MARGIN) // cw) - len(prompt) - len('echo ""')
        raise ValueError(f"tagline is {len(tagline)} characters; max is {max_chars} to fit {WIDTH}px")
    typed_w = len(typed) * cw
    x0 = (WIDTH - total_w) / 2
    x_typed = x0 + len(prompt) * cw
    x_end = x_typed + typed_w
    duration = len(typed) * SECONDS_PER_CHAR
    steps = f"{duration:.2f}s steps({len(typed)}, end) {START_DELAY}s both"
    css = (
        f"@keyframes type {{ from {{ transform: translateX(-{typed_w:.1f}px); }} }}\n"
        "@keyframes blink { 50% { opacity: 0; } }\n"
        f".typing {{ animation: type {steps}; }}\n"
        f".cursor {{ animation: type {steps}, blink 1s step-end {START_DELAY + duration:.2f}s infinite; }}"
    )
    body = (
        f'<rect width="{WIDTH}" height="{HEIGHT}" rx="8" fill="{BG}"/>'
        f'<text x="{x0:.1f}" y="{BASELINE}" font-size="{FONT_SIZE}" textLength="{len(prompt) * cw:.1f}" '
        f'xml:space="preserve"><tspan fill="{PROMPT}">{esc(prompt_user)}</tspan>'
        f'<tspan fill="{PATH_BLUE}"> ~</tspan><tspan fill="{TEXT}"> $ </tspan></text>'
        f'<text x="{x_typed:.1f}" y="{BASELINE}" font-size="{FONT_SIZE}" fill="{TEXT}" '
        f'textLength="{typed_w:.1f}" xml:space="preserve">{esc(typed)}</text>'
        f'<rect class="typing" x="{x_end:.1f}" y="10" width="{typed_w + cw:.1f}" height="36" fill="{BG}"/>'
        f'<rect class="cursor" x="{x_end:.1f}" y="{BASELINE - FONT_SIZE + 3}" width="{cw:.1f}" '
        f'height="{FONT_SIZE + 2}" fill="{TEXT}"/>'
        # border last so the resting cover rect never hides it
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="8" fill="none" stroke="{BORDER}"/>'
    )
    return svg_doc(WIDTH, HEIGHT, body, css)


def main() -> None:
    profile = load_profile()
    write_svg(ASSETS / "tagline.svg", render_tagline(profile["prompt"], profile["tagline"]))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run, expect PASS**; also `.venv/bin/python scripts/make_tagline.py` writes `assets/tagline.svg`.
- [ ] **Step 5: Commit**: `feat: self-hosted typing tagline SVG`

---

### Task 3: Neofetch info card

**Files:** Create `scripts/make_info_card.py`, `tests/test_info_card.py`

**Interfaces:**
- Consumes: `load_profile`, `svg_common.{ASSETS, DIM, KEY_COLORS, PROMPT, TEXT, char_width, esc, svg_doc, window_frame, wrap, write_svg}`
- Produces: `render_info_card(prompt_user: str, rows: list[list[str]]) -> str`; writes `assets/info-card.svg` (width 490, height computed).

- [ ] **Step 1: Write failing tests**: `tests/test_info_card.py`
```python
from make_info_card import WIDTH, render_info_card


def test_renders_every_key_and_value(check_svg, profile):
    svg = render_info_card(profile["prompt"], profile["card"])
    check_svg(svg, WIDTH)
    for key, _ in profile["card"]:
        assert f">{key}<" in svg
    assert "REST · GraphQL" in svg


def test_escapes_values(check_svg):
    svg = render_info_card("me", [["Key", "a & <b>"]])
    check_svg(svg)
    assert "a &amp; &lt;b&gt;" in svg


def test_long_value_wraps_and_card_grows(check_svg):
    short = render_info_card("me", [["Key", "short"]])
    long = render_info_card("me", [["Key", "word " * 40]])
    assert long.count('class="ln"') > short.count('class="ln"')
    assert int(check_svg(long).get("height")) > int(check_svg(short).get("height"))


def test_no_infinite_animation(profile):
    assert "infinite" not in render_info_card(profile["prompt"], profile["card"])
```

- [ ] **Step 2: Run, expect FAIL** (`ModuleNotFoundError: make_info_card`).

- [ ] **Step 3: Implement**: `scripts/make_info_card.py`
```python
"""Render assets/info-card.svg: a neofetch-style panel whose lines fade in one by one."""
from __future__ import annotations

from profile_data import load_profile
from svg_common import (ASSETS, DIM, KEY_COLORS, PROMPT, TEXT, char_width, esc, svg_doc,
                        window_frame, wrap, write_svg)

WIDTH = 490
FONT_SIZE = 12.5
LINE_HEIGHT = 21
PAD_X = 22
FIRST_BASELINE = 58
KEY_GAP_CHARS = 2
SWATCH_W, SWATCH_H = 26, 14
STAGGER = 0.12
START_DELAY = 0.4
CSS = (
    "@keyframes line { from { opacity: 0; transform: translateX(-6px); } }\n"
    ".ln { animation: line .35s ease-out both; }"
)


def _text(x: float, y: float, fill: str, text: str, bold: bool = False) -> str:
    weight = ' font-weight="bold"' if bold else ""
    return f'<text x="{x:.1f}" y="{y}" font-size="{FONT_SIZE}" fill="{fill}"{weight}>{esc(text)}</text>'


def _line(index: int, content: str) -> str:
    return f'<g class="ln" style="animation-delay:{START_DELAY + index * STAGGER:.2f}s">{content}</g>'


def _card_lines(prompt_user: str, rows: list[list[str]]) -> list[list[tuple]]:
    """Each output line as a list of (x, fill, text, bold) runs, wrapping long values."""
    cw = char_width(FONT_SIZE)
    value_x = PAD_X + (max(len(key) for key, _ in rows) + KEY_GAP_CHARS) * cw
    value_chars = int((WIDTH - PAD_X - value_x) // cw)
    lines = [[(PAD_X, PROMPT, prompt_user, True)], [(PAD_X, DIM, "─" * len(prompt_user), False)]]
    for i, (key, value) in enumerate(rows):
        color = KEY_COLORS[i % len(KEY_COLORS)]
        for j, part in enumerate(wrap(value, value_chars)):
            key_run = [(PAD_X, color, key, True)] if j == 0 else []
            lines.append(key_run + [(value_x, TEXT, part, False)])
    return lines


def render_info_card(prompt_user: str, rows: list[list[str]]) -> str:
    lines = _card_lines(prompt_user, rows)
    body = [
        _line(i, "".join(_text(x, FIRST_BASELINE + i * LINE_HEIGHT, fill, text, bold) for x, fill, text, bold in runs))
        for i, runs in enumerate(lines)
    ]
    swatch_y = FIRST_BASELINE + (len(lines) - 1) * LINE_HEIGHT + 14
    swatches = "".join(
        f'<rect x="{PAD_X + i * SWATCH_W}" y="{swatch_y}" width="{SWATCH_W}" height="{SWATCH_H}" fill="{color}"/>'
        for i, color in enumerate((*KEY_COLORS, TEXT, DIM))
    )
    body.append(_line(len(lines), swatches))
    height = swatch_y + SWATCH_H + 22
    frame = window_frame(WIDTH, height, f"{prompt_user}: ~")
    return svg_doc(WIDTH, height, frame + "".join(body), CSS)


def main() -> None:
    profile = load_profile()
    write_svg(ASSETS / "info-card.svg", render_info_card(profile["prompt"], profile["card"]))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run, expect PASS**; run `scripts/make_info_card.py`.
- [ ] **Step 5: Commit**: `feat: neofetch-style info card SVG`

---

### Task 4: Project cards

**Files:** Create `scripts/make_project_cards.py`, `tests/test_project_cards.py`

**Interfaces:**
- Consumes: `load_profile`, `svg_common.{ASSETS, DIM, LANG_COLORS, TEXT, char_width, esc, svg_doc, window_frame, wrap, write_svg}`
- Produces: `render_project_card(project: dict) -> str`; writes `assets/project-<slug>.svg` (280 wide).

- [ ] **Step 1: Write failing tests**: `tests/test_project_cards.py`
```python
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
```

- [ ] **Step 2: Run, expect FAIL** (`ModuleNotFoundError: make_project_cards`).

- [ ] **Step 3: Implement**: `scripts/make_project_cards.py`
```python
"""Render one terminal-window card per featured project: assets/project-<slug>.svg."""
from __future__ import annotations

from profile_data import load_profile
from svg_common import (ASSETS, DIM, LANG_COLORS, TEXT, char_width, esc, svg_doc, window_frame,
                        wrap, write_svg)

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
```

- [ ] **Step 4: Run, expect PASS**; run `scripts/make_project_cards.py` → 3 files.
- [ ] **Step 5: Commit**: `feat: terminal-window project cards`

---

### Task 5: Fetch and validate contributions

**Files:** Create `scripts/fetch_contributions.py`, `tests/test_contributions.py`

**Interfaces:**
- Produces: `Day(day: date, count: int, level: int)` (frozen dataclass); `CalendarError(ValueError)`; `parse_count(str)->int`; `parse_calendar(html)->list[Day]` (sorted); `validate_days(list[Day])->None`; `current_streak`, `longest_streak` `(list[Day])->int`; `best_day(list[Day])->Day|None`; `build_summary(list[Day])->dict` shaped `{"days":[{"date","count","level"}], "stats":{"total","current_streak","longest_streak","best_day":{"date","count"}|None}}`; `fetch_html(user)->str`; `main()->int`; module constant `DATA_PATH`.

- [ ] **Step 1: Write failing tests**: `tests/test_contributions.py`
```python
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
```

- [ ] **Step 2: Run, expect FAIL** (`ModuleNotFoundError: fetch_contributions`).

- [ ] **Step 3: Implement**: `scripts/fetch_contributions.py`
```python
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
```

- [ ] **Step 4: Run, expect PASS**; run `scripts/fetch_contributions.py` against the live endpoint.
- [ ] **Step 5: Commit**: `feat: fetch and validate public contribution calendar`

---

### Task 6: Heatmap SVG

**Files:** Create `scripts/render_heatmap_svg.py`, `tests/test_heatmap.py`

**Interfaces:**
- Consumes: summary dict from Task 5 (`data/contributions.json`), `svg_common.{ASSETS, BG, BORDER, DIM, HEAT_LEVELS, ROOT, TEXT, esc, svg_doc, write_svg}`
- Produces: `render_heatmap(summary: dict) -> str`, `place(days) -> list[tuple[int, int, dict]]` (col, row, day), `month_labels(placed) -> list[tuple[int, str]]`, `footer_lines(stats) -> tuple[str, str]`; constants `WIDTH`, `CELL`, `LABEL_W`; writes `assets/contrib-heatmap.svg` (860 wide).

- [ ] **Step 1: Write failing tests**: `tests/test_heatmap.py`
```python
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
```

- [ ] **Step 2: Run, expect FAIL** (`ModuleNotFoundError: render_heatmap_svg`).

- [ ] **Step 3: Implement**: `scripts/render_heatmap_svg.py`
```python
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
```

- [ ] **Step 4: Run, expect PASS**; run fetch then render; view `assets/contrib-heatmap.svg`.
- [ ] **Step 5: Commit**: `feat: animated contribution heatmap SVG`

---

### Task 7: ASCII portrait (local-only)

**Files:** Create `scripts/prep_photo.py`, `scripts/make_ascii_svg.py`, `tests/test_prep_photo.py`, `tests/test_ascii.py`

**Interfaces:**
- Produces: `prep_photo.subject_bbox(alpha, threshold=0.1) -> tuple[int,int,int,int]`, `square_crop(img, bbox, pad=0.06) -> ndarray`, `prep(photo: Image) -> ndarray`; `make_ascii_svg.RAMP`, `to_grid(gray, cols=90) -> list[str]`, `render_ascii(rows) -> str`; writes `assets/ascii-portrait.svg`.
- Heavy deps (`cv2`, `rembg`) are imported inside `prep()` so geometry tests need only numpy and Pillow.

- [ ] **Step 1: Install portrait deps**: `.venv/bin/pip install -q -r scripts/requirements-portrait.txt`

- [ ] **Step 2: Write failing tests**

`tests/test_prep_photo.py`
```python
import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("PIL")

from prep_photo import square_crop, subject_bbox  # noqa: E402


def test_subject_bbox():
    alpha = np.zeros((10, 20))
    alpha[2:5, 3:9] = 1
    assert subject_bbox(alpha) == (3, 2, 9, 5)


def test_empty_alpha_raises():
    with pytest.raises(ValueError, match="no subject"):
        subject_bbox(np.zeros((4, 4)))


def test_square_crop_pads_with_black_at_edges():
    img = np.full((10, 10), 200, dtype=np.uint8)
    out = square_crop(img, (0, 0, 10, 10), pad=0.1)
    assert out.shape == (12, 12)
    assert out[0, 0] == 0 and out[6, 6] == 200
```

`tests/test_ascii.py`
```python
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
```

- [ ] **Step 3: Run, expect FAIL** (`ModuleNotFoundError`).

- [ ] **Step 4: Implement**

`scripts/prep_photo.py`
```python
"""Local-only: isolate the subject of a portrait photo, boost contrast, and put it on black.

Writes .portrait/prepped.png (git-ignored). The original photo is never copied into the repo.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

from svg_common import ROOT

OUT_PATH = ROOT / ".portrait" / "prepped.png"
CLAHE_CLIP = 2.0
CLAHE_TILES = (8, 8)
CROP_PAD = 0.06
ALPHA_THRESHOLD = 0.1


def subject_bbox(alpha: np.ndarray, threshold: float = ALPHA_THRESHOLD) -> tuple[int, int, int, int]:
    ys, xs = np.nonzero(alpha > threshold)
    if xs.size == 0:
        raise ValueError("background removal found no subject")
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def square_crop(img: np.ndarray, bbox: tuple[int, int, int, int], pad: float = CROP_PAD) -> np.ndarray:
    """Square crop centred on bbox with padding; anything outside the image is black."""
    x0, y0, x1, y1 = bbox
    side = int(round(max(x1 - x0, y1 - y0) * (1 + 2 * pad)))
    left = int(round((x0 + x1) / 2 - side / 2))
    top = int(round((y0 + y1) / 2 - side / 2))
    canvas = np.zeros((side, side), dtype=img.dtype)
    sx0, sy0 = max(left, 0), max(top, 0)
    sx1, sy1 = min(left + side, img.shape[1]), min(top + side, img.shape[0])
    canvas[sy0 - top:sy1 - top, sx0 - left:sx1 - left] = img[sy0:sy1, sx0:sx1]
    return canvas


def prep(photo: Image.Image) -> np.ndarray:
    import cv2  # heavy, local-only dependencies
    from rembg import remove

    cut = np.asarray(remove(photo.convert("RGB")))
    alpha = cut[:, :, 3].astype(np.float32) / 255.0
    gray = cv2.cvtColor(np.ascontiguousarray(cut[:, :, :3]), cv2.COLOR_RGB2GRAY)
    contrast = cv2.createCLAHE(clipLimit=CLAHE_CLIP, tileGridSize=CLAHE_TILES).apply(gray)
    on_black = (contrast.astype(np.float32) * alpha).astype(np.uint8)
    return square_crop(on_black, subject_bbox(alpha))


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python scripts/prep_photo.py <photo>", file=sys.stderr)
        return 2
    src = Path(argv[1]).expanduser()
    if not src.is_file():
        print(f"prep_photo: no such file: {src}", file=sys.stderr)
        return 1
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(prep(Image.open(src))).save(OUT_PATH)
    print(f"prep_photo: wrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

`scripts/make_ascii_svg.py`
```python
"""Local-only: render .portrait/prepped.png as an ASCII portrait that prints itself row by row."""
from __future__ import annotations

import sys

import numpy as np
from PIL import Image

from svg_common import ASSETS, BG, ROOT, TEXT, char_width, esc, svg_doc, write_svg

PREPPED = ROOT / ".portrait" / "prepped.png"
RAMP = " .`:-=+*cs#%@"  # sparse -> dense; glyphs are light on dark, so bright pixels get dense glyphs
COLS = 90
FONT_SIZE = 10
LINE_HEIGHT = 10
PAD = 10
ROW_SECONDS = 0.35
ROW_STAGGER = 0.05


def to_grid(gray: np.ndarray, cols: int = COLS) -> list[str]:
    h, w = gray.shape
    glyph_aspect = char_width(FONT_SIZE) / LINE_HEIGHT
    rows = max(1, round(cols * (h / w) * glyph_aspect))
    small = np.asarray(Image.fromarray(gray).resize((cols, rows), Image.LANCZOS), dtype=np.float32) / 255.0
    idx = np.clip(np.rint(small * (len(RAMP) - 1)), 0, len(RAMP) - 1).astype(int)
    return ["".join(RAMP[i] for i in row) for row in idx]


def render_ascii(rows: list[str]) -> str:
    cw = char_width(FONT_SIZE)
    row_w = len(rows[0]) * cw
    width = round(row_w + 2 * PAD)
    height = len(rows) * LINE_HEIGHT + 2 * PAD
    css = (
        f"@keyframes wipe {{ from {{ transform: translateX(-{row_w:.1f}px); }} }}\n"
        f"@keyframes cur {{ 0% {{ transform: translateX(-{row_w:.1f}px); opacity: 0; }} 1% {{ opacity: 1; }} "
        "98% { opacity: 1; } 100% { transform: translateX(0); opacity: 0; } }\n"
        f".w {{ animation: wipe {ROW_SECONDS}s linear both; }}\n"
        f".k {{ opacity: 0; animation: cur {ROW_SECONDS}s linear both; }}"
    )
    parts = [f'<rect width="{width}" height="{height}" rx="8" fill="{BG}"/>']
    for i, row in enumerate(rows):
        y = PAD + i * LINE_HEIGHT
        delay = f'style="animation-delay:{i * ROW_STAGGER:.2f}s"'
        parts.append(
            f'<text x="{PAD}" y="{y + LINE_HEIGHT - 2}" font-size="{FONT_SIZE}" fill="{TEXT}" '
            f'textLength="{row_w:.1f}" lengthAdjust="spacing" xml:space="preserve">{esc(row)}</text>'
        )
        # cover and cursor rest just past the row end, so the static frame shows the whole portrait
        parts.append(f'<rect class="w" x="{PAD + row_w:.1f}" y="{y}" width="{row_w + cw:.1f}" height="{LINE_HEIGHT}" fill="{BG}" {delay}/>')
        parts.append(f'<rect class="k" x="{PAD + row_w:.1f}" y="{y}" width="{cw:.1f}" height="{LINE_HEIGHT}" fill="{TEXT}" {delay}/>')
    return svg_doc(width, height, "".join(parts), css)


def main() -> int:
    if not PREPPED.is_file():
        print(f"make_ascii_svg: {PREPPED} not found; run scripts/prep_photo.py <photo> first", file=sys.stderr)
        return 1
    gray = np.asarray(Image.open(PREPPED).convert("L"))
    write_svg(ASSETS / "ascii-portrait.svg", render_ascii(to_grid(gray)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run, expect PASS**: `.venv/bin/pytest -q`
- [ ] **Step 6: Generate**: `.venv/bin/python scripts/prep_photo.py ~/Downloads/IMG_6171.JPG && .venv/bin/python scripts/make_ascii_svg.py`; render a PNG preview and look at it. Tune `COLS`, CLAHE or crop if the face isn't readable; re-run tests after any change.
- [ ] **Step 7: Commit**: `feat: self-printing ASCII portrait pipeline` (confirm `git status` lists no image files)

---

### Task 8: README, cleanup, daily workflow, PR

**Files:** Modify `README.md`; delete old `assets/*` and `header.png`; create `.github/workflows/update-profile-art.yml`

- [ ] **Step 1: Remove old assets**: `git rm -q header.png` and every file under `assets/` except the 7 generated SVGs (`tagline`, `info-card`, `project-bit`, `project-tailormytext`, `project-movestar`, `contrib-heatmap`, `ascii-portrait`).

- [ ] **Step 2: Write `README.md`**
```html
<div align="center">

<img src="assets/tagline.svg" width="860" alt="moose@github ~ $ echo &quot;building things that ship&quot;" />

<h3><code>moose@github ~ $ ./contributions.sh</code></h3>

<img src="assets/contrib-heatmap.svg" width="860" alt="Contribution heatmap for the last year" />

<br><br>

<h3><code>moose@github ~ $ whoami</code></h3>

<table>
<tr>
<td valign="top"><img src="assets/ascii-portrait.svg" width="370" alt="ASCII portrait of Moose" /></td>
<td valign="top"><img src="assets/info-card.svg" width="490" alt="Full-stack engineer in NYC. Ruby, TypeScript, JavaScript, SQL; Rails, Angular, React, Node; PostgreSQL; REST and GraphQL." /></td>
</tr>
</table>

<br>

<h3><code>moose@github ~ $ ls ~/projects</code></h3>

<table>
<tr>
<td><a href="https://github.com/doosemavis/bit-design-system"><img src="assets/project-bit.svg" width="280" alt="bit-design-system" /></a></td>
<td><a href="https://github.com/doosemavis/tailormytext"><img src="assets/project-tailormytext.svg" width="280" alt="TailorMyText" /></a></td>
<td><a href="https://github.com/doosemavis/astro-clock"><img src="assets/project-movestar.svg" width="280" alt="MoveStar" /></a></td>
</tr>
</table>

</div>
```

- [ ] **Step 3: Write the workflow**: `.github/workflows/update-profile-art.yml`
```yaml
name: Update profile art

"on":
  schedule:
    - cron: "17 6 * * *"
  workflow_dispatch: {}
  push:
    branches: [main]
    paths:
      - profile.json
      - "scripts/**"
      - .github/workflows/update-profile-art.yml

permissions:
  contents: write

concurrency:
  group: profile-art
  cancel-in-progress: false

jobs:
  render:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
          cache-dependency-path: scripts/requirements.txt
      - run: pip install -r scripts/requirements.txt
      - run: python -m pytest -q
      - run: python scripts/make_tagline.py
      - run: python scripts/make_info_card.py
      - run: python scripts/make_project_cards.py
      - run: python scripts/fetch_contributions.py
      - run: python scripts/render_heatmap_svg.py
      - uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "chore: refresh profile art [skip ci]"
          file_pattern: "assets/*.svg data/contributions.json"
```

- [ ] **Step 4: Verify**: regenerate every SVG; `.venv/bin/pytest -q` all pass; simulate CI (fresh venv with only `requirements.txt` → portrait tests skip, rest pass); render each SVG to PNG and inspect; confirm `git ls-files | grep -iE '\.(jpe?g|png|heic)$'` is empty.
- [ ] **Step 5: Commit**: `feat: terminal-style README with daily heatmap workflow`
- [ ] **Step 6: Push and open PR**: `git push -u origin feat/terminal-readme`; `gh pr create --base main` with summary and test plan; owner previews the README on the branch before merging.
