"""Place the imagegen-corrected five-digit grip into the unchanged V2 sheet.

This is a local art composite, not a registration pass or game-ready sprite export.
The original V2 sheet and imagegen hand are both retained unchanged.
"""

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
BASE = HERE / "raw_two_pose_sheet_v2.png"
HAND = HERE / "raw_grip_five_digit_v1.png"
OUTPUT = HERE / "two_pose_v2_five_digit_grip_composite.png"
SOURCE_CROP = (245, 285, 765, 850)
TARGET_SIZE = (62, 65)
TARGET_XY = (693, 436)
CLEAR_RECT = (685, 430, 755, 508)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    with Image.open(BASE) as opened:
        sheet = opened.convert("RGBA")
    with Image.open(HAND) as opened:
        hand = opened.convert("RGBA")
    if sheet.size != (1207, 1303) or hand.size != (1300, 1210):
        raise ValueError("Input canvas changed; inspect anchors before placing the hand")

    crop = hand.crop(SOURCE_CROP)
    # Premultiplied resize preserves translucent edge colors.
    patch = crop.convert("RGBa").resize(TARGET_SIZE, Image.Resampling.LANCZOS).convert("RGBA")
    px = sheet.load()
    for y in range(CLEAR_RECT[1], CLEAR_RECT[3]):
        for x in range(CLEAR_RECT[0], CLEAR_RECT[2]):
            px[x, y] = (0, 0, 0, 0)
    sheet.alpha_composite(patch, TARGET_XY)
    sheet.save(OUTPUT, optimize=True)
    patch.save(HERE / "five_digit_grip_scaled_patch.png", optimize=True)

    before = Image.open(BASE).convert("RGBA")
    differences = np.any(np.asarray(before) != np.asarray(sheet), axis=2)
    ys, xs = np.nonzero(differences)
    allowed = np.zeros(differences.shape, dtype=bool)
    allowed[CLEAR_RECT[1]:CLEAR_RECT[3], CLEAR_RECT[0]:CLEAR_RECT[2]] = True
    detail_box = (670, 405, 815, 540)
    before.crop(detail_box).resize((580, 540), Image.Resampling.NEAREST).save(
        HERE / "five_digit_grip_before_x4.png", optimize=True)
    sheet.crop(detail_box).resize((580, 540), Image.Resampling.NEAREST).save(
        HERE / "five_digit_grip_after_x4.png", optimize=True)
    report = {
        "schema": "openyamm-pc01-five-digit-grip-composite-v1",
        "note": "Local art repair only. Original whole-pose mask registration still fails; do not install.",
        "base": {"path": BASE.name, "sha256": digest(BASE)},
        "generated_hand": {"path": HAND.name, "sha256": digest(HAND)},
        "source_crop": SOURCE_CROP, "target_size": TARGET_SIZE,
        "target_xy": TARGET_XY, "clear_rect": CLEAR_RECT,
        "output": {"path": OUTPUT.name, "sha256": digest(OUTPUT)},
        "validation": {"same_canvas": before.size == sheet.size,
                       "changed_pixels": int(len(xs)),
                       "changed_bbox": [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1],
                       "changed_pixels_outside_clear_rect": int(np.count_nonzero(differences & ~allowed))},
    }
    (HERE / "five_digit_grip_composite.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
