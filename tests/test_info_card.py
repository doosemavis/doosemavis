import pytest

from make_info_card import WIDTH, render_info_card

SAMPLE_ROWS = [["Langs", "Ruby · SQL"], ["APIs", "REST · GraphQL"]]


def test_real_profile_renders(check_svg, profile):
    check_svg(render_info_card(profile["prompt"], profile["card"]), WIDTH)


def test_renders_every_key_and_value(check_svg):
    svg = render_info_card("me", SAMPLE_ROWS)
    check_svg(svg, WIDTH)
    for key, value in SAMPLE_ROWS:
        assert f">{key}<" in svg and value in svg


def test_escapes_values(check_svg):
    svg = render_info_card("me", [["Key", "a & <b>"]])
    check_svg(svg)
    assert "a &amp; &lt;b&gt;" in svg


def test_long_value_wraps_and_card_grows(check_svg):
    short = render_info_card("me", [["Key", "short"]])
    long = render_info_card("me", [["Key", "word " * 40]])
    assert long.count('class="ln"') > short.count('class="ln"')
    assert int(check_svg(long).get("height")) > int(check_svg(short).get("height"))


def test_no_infinite_animation():
    assert "infinite" not in render_info_card("me", SAMPLE_ROWS)


def test_prompt_too_wide_raises():
    with pytest.raises(ValueError, match="prompt"):
        render_info_card("p" * 70, [["Key", "value"]])


def test_key_too_long_raises_naming_the_key():
    with pytest.raises(ValueError, match="card key"):
        render_info_card("me", [["K" * 50, "value"]])
