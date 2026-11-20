"""Split the pilot's generated sheets into 118x158 RGBA frames registered to the pc07 template.

Registration follows the accepted 2026-09-27 run in spirit: generated alpha is kept untouched, the bottom contact
matches the template frame and the silhouette is centred on the template's centre. One uniform scale serves all 56
frames (HEAD_FIT times the median template-height fit), so the head keeps its size through every animation; heads
are shifted inward to stay on the canvas and only those wider than the canvas are clipped, evenly. The ducking
dodge frames (35, 36) match the template's crown instead and sink out of the bottom of the frame. Targeted
regenerations (REPAIRS) replace their slots, scaled so their frontal head matches frame 01.
Writes frames/, a comparison plate and report.json.
"""

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
HUD = HERE.parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HUD))
from extract_transparent_portraits import sheet_geometry  # noqa: E402

SIZE = (118, 158)
TEMPLATE = ROOT / "assets_dev/engine/icons_x2"
MM9 = ROOT / "mm9/extracted/ART/ART/PCPORTRAITS/PC03"
PARTIAL = {35, 36}
# Targeted regenerations: folder -> slots left to right, and the frontal slot that sets the repair's scale.
REPAIRS = {"repair_18_48": [18, 48]}
REPAIR_FRONTAL = {"repair_18_48": 48}
HEAD_FIT = 0.96  # this face is wider than pc07 at equal height; trade 4% height for less clipping


def body_box(alpha):
    labels, _ = ndimage.label(alpha >= 128, structure=np.ones((3, 3)))
    sizes = np.bincount(labels.ravel())
    sizes[0] = 0
    ys, xs = np.where(labels == sizes.argmax())
    return [int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)]


def resample(cell, scale, offset):
    border = max(cell.size)
    padded = Image.new("RGBA", (cell.width + 2 * border, cell.height + 2 * border))
    padded.paste(cell, (border, border))
    x, y = offset
    window = (border - x / scale, border - y / scale,
              border + (SIZE[0] - x) / scale, border + (SIZE[1] - y) / scale)
    return padded.convert("RGBa").resize(SIZE, Image.Resampling.LANCZOS, box=window).convert("RGBA")


def main():
    mapping = json.loads((HERE / "mapping.json").read_text())
    (HERE / "frames").mkdir(exist_ok=True)
    report = {}
    cells = []
    for letter, first in (("A", 1), ("B", 29)):
        raw = Image.open(HERE / f"raw_{letter}.png")
        report[letter] = {"raw_size": raw.size, "raw_mode": raw.mode}
        raw = raw.convert("RGBA")
        columns, rows, issues = sheet_geometry(raw)
        report[letter]["grid_issues"] = issues
        for slot in range(28):
            number = first + slot
            rect = [columns[slot % 7], rows[slot // 7], columns[slot % 7 + 1], rows[slot // 7 + 1]]
            cell = raw.crop(rect)
            master = body_box(np.asarray(cell.getchannel("A")))
            template = Image.open(TEMPLATE / f"pc07-{number:02d}.png").convert("RGBA")
            target = body_box(np.asarray(template.getchannel("A")))
            fit = (target[3] - target[1]) / (master[3] - master[1])
            cells.append((letter, number, cell, master, target, fit))
    # One head size for the whole character, so the head never pulses between frames.
    scale = HEAD_FIT * float(np.median([c[5] for c in cells if c[1] not in PARTIAL]))
    neutral = next(c for c in cells if c[1] == 1)
    scales = {}
    for folder, numbers in REPAIRS.items():
        raw_path = HERE / folder / "raw.png"
        if not raw_path.exists():
            continue
        raw = Image.open(raw_path).convert("RGBA")
        alpha = np.asarray(raw.getchannel("A"))
        # Split the row at the emptiest column of the middle half.
        occupancy = (alpha > 8).sum(axis=0)
        quarter = raw.width // 4
        cut = quarter + int(np.argmin(occupancy[quarter:3 * quarter]))
        repaired = []
        for number, rect in zip(numbers, ([0, 0, cut, raw.height], [cut, 0, raw.width, raw.height])):
            cell = raw.crop(rect)
            master = body_box(np.asarray(cell.getchannel("A")))
            template = Image.open(TEMPLATE / f"pc07-{number:02d}.png").convert("RGBA")
            repaired.append((folder, number, cell, master, body_box(np.asarray(template.getchannel("A"))), None))
        # Repairs come at their own resolution: the frontal repair head gets frame 01's output height.
        frontal = next(r for r in repaired if r[1] == REPAIR_FRONTAL[folder])
        for item in repaired:
            scales[item[1]] = scale * (neutral[3][3] - neutral[3][1]) / (frontal[3][3] - frontal[3][1])
        report[folder] = {"cut_column": cut}
        cells = [c for c in cells if c[1] not in numbers] + repaired
    for letter, number, cell, master, target, fit in sorted(cells, key=lambda c: c[1]):
        scale_used = scales.get(number, scale)
        width = scale_used * (master[2] - master[0])
        left = (target[0] + target[2]) / 2 - width / 2
        # Shift inward to keep a one-pixel margin; a head wider than the canvas is centred and clipped evenly.
        left = (SIZE[0] - width) / 2 if width > SIZE[0] - 2 else min(max(left, 1), SIZE[0] - 1 - width)
        # Dodge frames duck out of the bottom of the frame: match the template's crown and let the canvas clip
        # the rest. Every other frame sits on the template's bottom contact.
        top = target[1] - scale_used * master[1] if number in PARTIAL else target[3] - scale_used * master[3]
        offset = left - scale_used * master[0], top
        frame = resample(cell, scale_used, offset)
        frame.save(HERE / "frames" / f"mm9pc03-{number:02d}.png")
        out = body_box(np.asarray(frame.getchannel("A")))
        report.setdefault(letter, {})[f"{number:02d}"] = {
            "meaning": mapping[str(number)]["meaning"], "master_box": master, "template_box": target,
            "output_box": out, "own_height_fit": None if fit is None else round(fit, 4),
            "scale": round(scale_used, 4),
            "clipped_px": round(max(0.0, width - SIZE[0]), 1),
            "master_px_per_native": round(1 / scale_used * 2, 2),
            "transparent_fraction": round(float(np.mean(np.asarray(frame.getchannel("A")) == 0)), 3)}
    (HERE / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    plate()


def plate():
    """Per slot: MM9 source, pc07 template, new frame on grey, new frame on the dark HUD tone."""
    mapping = json.loads((HERE / "mapping.json").read_text())
    cw, ch, cols = 118, 158, 7
    for letter, first in (("A", 1), ("B", 29)):
        image = Image.new("RGB", (cols * (4 * cw + 12), 4 * (ch + 18)), (24, 24, 24))
        draw = ImageDraw.Draw(image)
        for slot in range(28):
            number = first + slot
            x0 = slot % cols * (4 * cw + 12)
            y0 = slot // cols * (ch + 18)
            info = mapping[str(number)]
            mm9 = Image.open(MM9 / f"PC-03-{info['mm9_frame']:02d}.pcx").convert("RGB")
            image.paste(mm9.resize((120, 160), Image.Resampling.NEAREST).crop((1, 1, 119, 159)), (x0, y0 + 18))
            for k, (path, bg) in enumerate(((TEMPLATE / f"pc07-{number:02d}.png", (90, 90, 90)),
                                            (HERE / "frames" / f"mm9pc03-{number:02d}.png", (90, 90, 90)),
                                            (HERE / "frames" / f"mm9pc03-{number:02d}.png", (20, 18, 24)))):
                tile = Image.new("RGB", (cw, ch), bg)
                frame = Image.open(path).convert("RGBA")
                tile.paste(frame, (0, 0), frame)
                image.paste(tile, (x0 + (k + 1) * cw, y0 + 18))
            draw.text((x0 + 2, y0 + 3), f"{number:02d} {info['meaning']} (mm9 {info['mm9_frame']})",
                      fill=(255, 220, 0))
        image.save(HERE / f"comparison_{letter}.png")


if __name__ == "__main__":
    main()
