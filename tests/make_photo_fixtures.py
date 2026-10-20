#!/usr/bin/env python3
"""Generate a small synthetic photo test set (no real client photos).

Usage: python3 tests/make_photo_fixtures.py OUT_DIR
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo

try:
    import pillow_heif  # type: ignore
    pillow_heif.register_heif_opener()
    HEIC = True
except Exception:  # pragma: no cover
    HEIC = False


def scene(seed, w=2000, h=1500):
    rng = np.random.default_rng(seed)
    img = np.full((h, w, 3), rng.integers(90, 170, 3), dtype=np.uint8)
    for _ in range(60):
        c = tuple(int(x) for x in rng.integers(0, 255, 3))
        x1, y1 = int(rng.integers(0, w)), int(rng.integers(0, h))
        x2, y2 = x1 + int(rng.integers(40, 500)), y1 + int(rng.integers(40, 400))
        if rng.random() < 0.5:
            cv2.rectangle(img, (x1, y1), (x2, y2), c, -1)
        else:
            cv2.circle(img, (x1, y1), int(rng.integers(20, 200)), c, -1)
    noise = rng.normal(0, 6, img.shape)
    return np.clip(img + noise, 0, 255).astype(np.uint8)


def camera_exif(gps=False):
    ex = Image.Exif()
    ex[271] = "Apple"
    ex[272] = "iPhone 15"
    if gps:
        ex[34853] = {1: "N", 2: (51.0, 45.0, 10.0), 3: "W", 4: (0.0, 20.0, 5.0)}
    return ex


def save_jpg(arr, path, exif=None):
    im = Image.fromarray(arr)
    if exif is not None:
        im.save(path, "JPEG", quality=92, exif=exif)
    else:
        im.save(path, "JPEG", quality=92)


def build(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for i in range(1, 10):
        save_jpg(scene(i), out / f"job_{i:02d}.jpg", camera_exif(gps=(i == 1)))
    blurred = cv2.GaussianBlur(scene(50), (0, 0), 12)
    save_jpg(blurred, out / "blurred.jpg", camera_exif())
    save_jpg((scene(51) * 0.22).astype(np.uint8), out / "dark.jpg", camera_exif())
    dup = cv2.resize(np.clip(scene(1).astype(int) + 8, 0, 255).astype(np.uint8), (1800, 1350))
    save_jpg(dup, out / "job_01_copy.jpg", camera_exif())
    shot = np.full((2532, 1170, 3), 245, dtype=np.uint8)
    shot[90:, :] = scene(60, 1170, 2442)
    cv2.putText(shot, "9:41", (40, 62), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (0, 0, 0), 4)
    cv2.rectangle(shot, (1020, 30), (1110, 62), (0, 0, 0), -1)
    Image.fromarray(shot).save(out / "screenshot.png")
    odd = np.full((2000, 1000, 3), 250, dtype=np.uint8)
    odd[70:, :] = scene(61, 1000, 1930)
    cv2.putText(odd, "10:02", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 3)
    Image.fromarray(odd).save(out / "screenshot_odd_size.png")
    save_jpg(scene(70, 1600, 1200), out / "IMG-20261020-WA0001.jpg")
    save_jpg(scene(71, 2000, 1500), out / "no_exif_photo.jpg")
    Image.fromarray(scene(80, 120, 40)).save(out / "signature.png")
    Image.fromarray(scene(81, 1200, 900)).save(out / "fake_is_png.jpg", "PNG")
    (out / "logo.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>')
    info = PngInfo()
    info.add_text("parameters", "a modern bathroom, Stable Diffusion, steps 30")
    Image.fromarray(scene(90, 1600, 1200)).save(out / "ai_render.png", pnginfo=info)
    Image.fromarray(scene(91, 380, 300)).save(out / "tiny.jpg", "JPEG", quality=95)
    if HEIC:
        Image.fromarray(scene(95)).save(out / "iphone.heic", exif=camera_exif(gps=True))
    return out


if __name__ == "__main__":
    print(build(sys.argv[1]))
