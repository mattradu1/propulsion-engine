---
name: photo-scorer
description: Use whenever client photos land in Clients/{record ID}/Inbox (or a test folder) to score them usable/low/reject, find duplicates and screenshots, flag no-camera-data and AI-tagged images, strip location data on export, and recommend standard vs lowPhoto layout. Tidy only; never alters the work.
---
# Photo scorer (rulebook S1 machine, S2 rules)

## Run
```
python3 scripts/photo_score.py <folder> --record-id REC-0101 \
    [--labels labels.json] [--export <clean-folder>]
```
- `--labels`: {"file.jpg": ["finished_job", ...]} from the model step or Matt. The layout is
  `standard` only with 8+ usable including one labelled finished job.
- `--export`: re-saves usable and low images as JPEG with all metadata removed (location included),
  orientation applied, named `{record_id}-{hash}.jpg`. Only exported copies go to the build. HEIC is
  converted (pillow-heif installed 19 Oct; if missing the output says so).
- The folder must be a copy staged locally; this script never reads Drive.

## Reading the output
- `reject`: AI tag (never used), too small, very blurry/dark, near-duplicate (best one kept),
  undecodable. `quarantine`: SVG/HTML/XML/zip or contents that don't match the extension: never opened.
- `low`: blurry, dark, small, screenshot (a screenshot of a website/preview is feedback, not a photo),
  WhatsApp-compressed, no camera data (never the hero; only after Matt's Saturday tick AND the client's
  written origin answer).
- `skipped`: signature-size images, never counted.
- `summary.no_camera_data > 0`: the photo-origin question goes as the Still needed line (approved).
- 200+ photos: the model sees only `summary.model_shortlist` (top 30).
- Not checked by this script (needs a model step or Matt, needs testing): faces (consent check), plates
  and house numbers (blur), paperwork, other firms' branding, unsafe working, the finished-job label.

Never generate, add fittings, remove defects or hide anything. Tests (synthetic images only):
`python3 -m unittest tests/test_photo_score.py`; make a sample set with
`python3 tests/make_photo_fixtures.py <dir>`.
