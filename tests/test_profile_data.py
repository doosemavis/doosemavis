import pytest

from profile_data import ProfileError, load_profile, validate_profile


def test_repo_profile_is_valid():
    data = load_profile()
    assert data["card"] and data["projects"]


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
