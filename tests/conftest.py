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
