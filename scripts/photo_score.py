#!/usr/bin/env python3
"""S1 Photo scorer. Tidy-only: it never generates or alters the work.

Scores every file in a folder and prints JSON: usable / low / reject (plus
skipped signature images and quarantined files), each with reasons, and a
layout recommendation (standard vs lowPhoto, S2 rules).

Checks: sharpness (Laplacian variance), brightness, resolution, orientation,
near-duplicates (difference hash), screenshots (exact phone screen sizes and a
status-bar heuristic), WhatsApp compression pattern, no camera data, AI tags,
real file type vs extension (SVG/HTML/XML/zip and mismatches quarantined),
HEIC via pillow-heif when installed.

--export DIR re-saves every usable/low image as JPEG with ALL metadata removed
(location included), orientation applied, named {record_id}-{hash}.jpg, and
verifies the saved copy has no location data.

Not done here (needs a model or Matt, needs testing): faces, number plates,
paperwork, other firms' branding, unsafe working, "finished job" judgement.
Pass --labels labels.json ({"file.jpg": ["finished_job", ...]}) to supply them.

Usage: python3 scripts/photo_score.py FOLDER [--labels L.json] [--export DIR]
                                       [--record-id REC-0001]
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

try:
    import pillow_heif  # type: ignore
    pillow_heif.register_heif_opener()
    HEIC_SUPPORT = True
except Exception:  # pragma: no cover
    HEIC_SUPPORT = False

IMAGE_EXT = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP", ".heic": "HEIF", ".heif": "HEIF"}
QUARANTINE_EXT = {".svg", ".html", ".htm", ".xml", ".zip", ".exe", ".js", ".docm", ".xlsm", ".dat"}

SIGNATURE_MAX_BYTES = 15_000
SIGNATURE_MAX_SIDE = 300
SHARP_LOW = 60.0
SHARP_REJECT = 8.0
DARK_LOW = 55.0
DARK_REJECT = 18.0
BRIGHT_LOW = 225.0
SHORT_SIDE_LOW = 700
LONG_SIDE_REJECT = 400
HERO_LONG_SIDE = 1600
DUP_HAMMING = 8
MODEL_TOP_N = 30

PHONE_SCREENS = {
    (750, 1334), (828, 1792), (1080, 1920), (1080, 2340), (1080, 2400), (1125, 2436), (1170, 2532),
    (1179, 2556), (1206, 2622), (1242, 2208), (1242, 2688), (1284, 2778), (1290, 2796), (1320, 2868),
    (1440, 2960), (1440, 3040), (1440, 3088), (1440, 3200), (720, 1600), (1080, 2160), (1080, 2408),
}
WHATSAPP_RE = re.compile(r"^(IMG-\d{8}-WA\d{3,5}|WhatsApp Image .*)", re.I)
AI_MARKERS = [b"trainedAlgorithmicMedia", b"c2pa", b"Midjourney", b"DALL-E", b"DALL\xc2\xb7E",
              b"Stable Diffusion", b"Adobe Firefly", b"compositeWithTrainedAlgorithmicMedia", b"openai"]
TAG_MAKE, TAG_MODEL, TAG_DATETIME_ORIG, TAG_GPS, TAG_EXIF_IFD = 271, 272, 36867, 34853, 34665


def sniff(path):
    head = path.read_bytes()[:512]
    low = head.lower()
    if head.startswith(b"PK\x03\x04"):
        return "zip"
    if b"<svg" in low:
        return "svg"
    if low.lstrip().startswith(b"<?xml"):
        return "xml"
    if b"<html" in low or b"<!doctype html" in low:
        return "html"
    if head.startswith(b"MZ"):
        return "exe"
    return None


def dhash(gray_img):
    small = cv2.resize(gray_img, (9, 8), interpolation=cv2.INTER_AREA)
    bits = (small[:, 1:] > small[:, :-1]).flatten()
    return int("".join("1" if b else "0" for b in bits), 2)


def hamming(a, b):
    return bin(a ^ b).count("1")


def status_bar_like(gray):
    """A screenshot's status bar: a flat band at the very top with small,
    high-contrast marks (clock, battery), sharply different texture below."""
    h = gray.shape[0]
    band = gray[: max(8, int(h * 0.035)), :]
    med = np.median(band)
    flat = np.mean(np.abs(band.astype(int) - med) < 12)
    marks = np.mean(np.abs(band.astype(int) - med) > 80)
    return flat > 0.85 and 0.003 < marks < 0.15


def camera_data(exif):
    if exif is None:
        return False
    if exif.get(TAG_MAKE) or exif.get(TAG_MODEL):
        return True
    try:
        sub = exif.get_ifd(TAG_EXIF_IFD)
        return bool(sub.get(TAG_DATETIME_ORIG))
    except Exception:
        return False


def has_location(exif):
    if exif is None:
        return False
    try:
        gps = exif.get_ifd(TAG_GPS)
        if gps:
            return True
    except Exception:
        pass
    return TAG_GPS in exif


def ai_tag(path, img):
    raw = path.read_bytes()
    for m in AI_MARKERS:
        if m.lower() in raw.lower():
            return m.decode("utf-8", "ignore")
    info = getattr(img, "info", {}) or {}
    for k, v in info.items():
        if str(k).lower() in ("parameters", "prompt", "workflow", "dream"):
            return f"text chunk '{k}'"
        if isinstance(v, (str, bytes)) and any(m.lower() in (v if isinstance(v, bytes) else v.encode()).lower()
                                               for m in AI_MARKERS):
            return f"text chunk '{k}'"
    return None


def score_file(path):
    r = {"file": path.name, "label": None, "reasons": [], "flags": []}
    ext = path.suffix.lower()
    size = path.stat().st_size
    kind = sniff(path)
    if ext in QUARANTINE_EXT or kind:
        r.update(label="quarantine", reasons=[f"{kind or ext} file: quarantined, never opened or counted"])
        return r
    if ext not in IMAGE_EXT:
        r.update(label="quarantine", reasons=[f"{ext or 'no extension'} isn't an image type"])
        return r
    if ext in (".heic", ".heif") and not HEIC_SUPPORT:
        r.update(label="low", reasons=["HEIC: pillow-heif not installed, can't convert here (needs testing)"])
        return r
    try:
        img = Image.open(path)
        img.load()
    except Exception as exc:
        r.update(label="reject", reasons=[f"can't be decoded: {exc.__class__.__name__}"])
        return r
    fmt = (img.format or "").upper()
    expect = IMAGE_EXT[ext]
    if not (fmt == expect or (expect == "HEIF" and fmt in ("HEIF", "HEIC"))):
        r.update(label="quarantine", reasons=[f"contents are {fmt or 'unknown'} but the name says {ext}"])
        return r

    exif = img.getexif()
    cam = camera_data(exif)
    loc = has_location(exif)
    ai = ai_tag(path, img)
    img_t = ImageOps.exif_transpose(img)
    w, h = img_t.size
    r.update(width=w, height=h, bytes=size, format=fmt, camera_data=cam, location_data=loc,
             orientation="landscape" if w > h else "portrait" if h > w else "square")

    if size < SIGNATURE_MAX_BYTES or max(w, h) < SIGNATURE_MAX_SIDE:
        r.update(label="skipped", reasons=["under the minimum size: treated as a signature image, never counted"])
        return r

    rgb = np.array(img_t.convert("RGB"))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    scale = 1024 / max(w, h)
    g_small = cv2.resize(gray, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_AREA) \
        if scale < 1 else gray
    sharp = float(cv2.Laplacian(g_small, cv2.CV_64F).var())
    bright = float(g_small.mean())
    r.update(sharpness=round(sharp, 1), brightness=round(bright, 1), dhash=f"{dhash(g_small):016x}")

    label = "usable"
    reasons = []

    def worse(new, why):
        nonlocal label
        order = {"usable": 0, "low": 1, "reject": 2}
        if order[new] > order[label]:
            label = new
        reasons.append(why)

    if ai:
        worse("reject", f"AI tag found ({ai}): never used")
    if max(w, h) < LONG_SIDE_REJECT:
        worse("reject", f"too small ({w}x{h})")
    elif min(w, h) < SHORT_SIDE_LOW:
        worse("low", f"small ({w}x{h}): small slots only")
    if sharp < SHARP_REJECT:
        worse("reject", f"very blurry (sharpness {sharp:.0f})")
    elif sharp < SHARP_LOW:
        worse("low", f"blurry (sharpness {sharp:.0f}): never the hero")
    if bright < DARK_REJECT:
        worse("reject", f"too dark to rescue (brightness {bright:.0f})")
    elif bright < DARK_LOW:
        worse("low", f"dark (brightness {bright:.0f}): brightness tidy allowed, never the hero if still weak")
    elif bright > BRIGHT_LOW:
        worse("low", f"overexposed (brightness {bright:.0f})")

    screen = (min(w, h), max(w, h)) in PHONE_SCREENS
    if not cam and (screen or (fmt == "PNG" and status_bar_like(gray))):
        worse("low", "screenshot: if it shows a website or preview it's feedback (change requests), "
                     "never a site photo")
        r["flags"].append("screenshot")
    if not cam and WHATSAPP_RE.match(path.stem):
        worse("low", "WhatsApp-compressed: small slots only, after Matt's Saturday tick")
        r["flags"].append("whatsapp")
    if not cam:
        r["flags"].append("no_camera_data")
        if "screenshot" not in r["flags"] and "whatsapp" not in r["flags"]:
            worse("low", "no camera data: never the hero; used only after Matt's Saturday tick and the "
                         "client's written origin answer")
    if loc:
        r["flags"].append("location_data: stripped on export")
    if ext in (".heic", ".heif"):
        r["flags"].append("heic: converted to JPG on export")

    quality = min(sharp, 600) / 600 * 0.5 + (1 - abs(bright - 128) / 128) * 0.25 + min(min(w, h), 1500) / 1500 * 0.25
    r.update(label=label, reasons=reasons or ["sharp, well lit, big enough"], quality=round(quality, 3),
             hero_ok=bool(label == "usable" and cam and max(w, h) >= HERO_LONG_SIDE and sharp >= SHARP_LOW * 2))
    return r


def mark_duplicates(results):
    scored = [r for r in results if r.get("dhash") and r["label"] in ("usable", "low")]
    scored.sort(key=lambda r: (-{"usable": 1, "low": 0}[r["label"]], -r["quality"]))
    kept = []
    for r in scored:
        h = int(r["dhash"], 16)
        twin = next((k for k in kept if hamming(h, int(k["dhash"], 16)) <= DUP_HAMMING), None)
        if twin:
            r["label"] = "reject"
            if r["reasons"] == ["sharp, well lit, big enough"]:
                r["reasons"] = []
            r["reasons"].append(f"near-duplicate of {twin['file']}: best one kept")
            r["hero_ok"] = False
        else:
            kept.append(r)


def layout(results, labels):
    usable = [r for r in results if r["label"] == "usable"]
    finished = [r for r in usable if "finished_job" in labels.get(r["file"], [])]
    n = len(usable)
    if n >= 8 and finished:
        return {"layout": "standard", "reason": f"{n} usable including a finished job"}
    if n >= 8:
        return {"layout": "lowPhoto", "reason": f"{n} usable but no photo labelled as a finished job yet",
                "ask": "one finished-job shot, as the Still needed line"}
    if n >= 3:
        return {"layout": "lowPhoto", "reason": f"{n} usable (3 to 7)", "ask": "the missing slot"}
    return {"layout": "lowPhoto", "reason": f"{n} usable (fewer than 3): text or van/team hero",
            "ask": "one exact shot, asked once"}


def export(results, folder, out_dir, record_id):
    out_dir.mkdir(parents=True, exist_ok=True)
    for r in results:
        if r["label"] not in ("usable", "low") or "width" not in r:
            continue
        src = folder / r["file"]
        img = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
        clean = Image.new("RGB", img.size)
        clean.paste(img)
        digest = hashlib.sha256(src.read_bytes()).hexdigest()[:12]
        dest = out_dir / f"{record_id}-{digest}.jpg"
        clean.save(dest, "JPEG", quality=88, optimize=True)  # no exif= : all metadata dropped
        check = Image.open(dest)
        r["exported"] = str(dest)
        r["export_location_stripped"] = not has_location(check.getexif()) and len(check.getexif()) == 0


def score_folder(folder, labels=None, export_dir=None, record_id="REC"):
    folder = Path(folder)
    labels = labels or {}
    results = [score_file(p) for p in sorted(folder.iterdir()) if p.is_file() and not p.name.startswith(".")]
    mark_duplicates(results)
    if export_dir:
        export(results, folder, Path(export_dir), record_id)
    counts = {k: sum(1 for r in results if r["label"] == k) for k in ("usable", "low", "reject", "skipped",
                                                                         "quarantine")}
    ranked = sorted((r for r in results if r["label"] in ("usable", "low")), key=lambda r: -r["quality"])
    summary = dict(counts)
    summary.update(
        labelled_usable=sum(1 for r in results if r["label"] == "usable" and labels.get(r["file"])),
        no_camera_data=sum(1 for r in results if "no_camera_data" in r.get("flags", [])),
        hero_candidates=[r["file"] for r in ranked if r.get("hero_ok")][:5],
        model_shortlist=[r["file"] for r in ranked][:MODEL_TOP_N],
        heic_support=HEIC_SUPPORT,
        not_checked="faces, number plates, paperwork, other firms' branding, unsafe working: needs a model step "
                    "or Matt (needs testing)",
    )
    summary.update(layout(results, labels))
    return {"folder": str(folder), "summary": summary, "photos": results}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Score a folder of client photos")
    ap.add_argument("folder")
    ap.add_argument("--labels")
    ap.add_argument("--export")
    ap.add_argument("--record-id", default="REC")
    a = ap.parse_args(argv)
    labels = json.loads(Path(a.labels).read_text()) if a.labels else {}
    print(json.dumps(score_folder(a.folder, labels, a.export, a.record_id), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
