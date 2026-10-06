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
