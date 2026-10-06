import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("PIL")

from prep_photo import apply_black_point, apply_gamma, face_crop_box, square_crop, subject_bbox  # noqa: E402


def test_gamma_below_one_lifts_midtones_and_keeps_endpoints():
    out = apply_gamma(np.array([0, 128, 255], dtype=np.uint8), gamma=0.75)
    assert out[0] == 0 and out[2] == 255 and out[1] > 128


def test_black_point_blanks_shadows_and_keeps_highlights():
    out = apply_black_point(np.array([0, 30, 40, 147, 255], dtype=np.uint8), black_point=40)
    assert out.tolist() == [0, 0, 0, 126, 255]


def test_face_crop_box_is_square_and_sits_below_the_face_centre():
    x0, y0, x1, y1 = face_crop_box((100, 100, 50, 50), scale=2.6, drop=0.35)
    assert x1 - x0 == y1 - y0 == 130
    assert (x0 + x1) / 2 == 125 and (y0 + y1) / 2 > 125


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
