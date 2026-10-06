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
