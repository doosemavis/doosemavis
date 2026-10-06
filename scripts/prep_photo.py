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
BLACK_POINT = 20  # anything darker prints as blank space instead of a sea of dots
GAMMA = 0.75  # < 1 lifts midtones so the shadowed side of the face still prints
FACE_SCALE = 2.6  # crop side, in detected-face heights
FACE_DROP = 0.35  # shift the crop below the face centre, in face heights, to keep chin and hands
FACE_CASCADE = "haarcascade_frontalface_default.xml"


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


def apply_black_point(gray: np.ndarray, black_point: int = BLACK_POINT) -> np.ndarray:
    """Clip everything at or below black_point to 0 and stretch the rest back to 0-255."""
    stretched = (gray.astype(np.float32) - black_point) * 255.0 / (255 - black_point)
    return np.clip(stretched, 0, 255).astype(np.uint8)


def apply_gamma(gray: np.ndarray, gamma: float = GAMMA) -> np.ndarray:
    return (np.power(gray.astype(np.float32) / 255.0, gamma) * 255.0).round().astype(np.uint8)


def face_crop_box(face: tuple[int, int, int, int], scale: float = FACE_SCALE,
                  drop: float = FACE_DROP) -> tuple[int, int, int, int]:
    """Square box around a detected face (x, y, w, h), nudged down to include chin and hands."""
    x, y, w, h = face
    half = h * scale / 2
    cx, cy = x + w / 2, y + h / 2 + h * drop
    return round(cx - half), round(cy - half), round(cx + half), round(cy + half)


def _largest_face(gray: np.ndarray) -> tuple[int, int, int, int] | None:
    import cv2

    detector = cv2.CascadeClassifier(cv2.data.haarcascades + FACE_CASCADE)
    faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6, minSize=(60, 60))
    if len(faces) == 0:
        return None
    return tuple(int(v) for v in max(faces, key=lambda f: f[2] * f[3]))


def prep(photo: Image.Image) -> np.ndarray:
    import cv2  # heavy, local-only dependencies
    from rembg import remove

    rgb = photo.convert("RGB")
    cut = np.asarray(remove(rgb))
    alpha = cut[:, :, 3].astype(np.float32) / 255.0
    gray = cv2.cvtColor(np.ascontiguousarray(cut[:, :, :3]), cv2.COLOR_RGB2GRAY)
    contrast = cv2.createCLAHE(clipLimit=CLAHE_CLIP, tileGridSize=CLAHE_TILES).apply(gray)
    on_black = (contrast.astype(np.float32) * alpha).astype(np.uint8)
    face = _largest_face(cv2.cvtColor(np.asarray(rgb), cv2.COLOR_RGB2GRAY))
    cropped = (square_crop(on_black, face_crop_box(face), pad=0) if face
               else square_crop(on_black, subject_bbox(alpha)))
    return apply_gamma(apply_black_point(cropped))


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
