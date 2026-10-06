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


def _non_empty_str(value: object) -> bool:
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
