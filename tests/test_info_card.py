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
