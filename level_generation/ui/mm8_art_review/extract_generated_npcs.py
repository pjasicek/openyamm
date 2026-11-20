"""Extract individual exact-2x review candidates from new NPC master sheets."""

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from extract_raw_buttons import crop_cell, fit_candidate, read_catalog


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def boundary(profile, expected, direction, radius):
    radius_pixels = 3
    start = max(radius_pixels, expected - radius)
    stop = min(len(profile) - radius_pixels, expected + radius)
    return max(
        (direction * (profile[index:index + radius_pixels].mean()
                      - profile[index - radius_pixels:index].mean()), index)
        for index in range(start, stop)
    )


def opaque_paint_mask(raw):
    pixels = np.asarray(raw.convert("RGB"), dtype=np.int16)
    border = np.concatenate((pixels[:4].reshape(-1, 3), pixels[-4:].reshape(-1, 3),
                             pixels[:, :4].reshape(-1, 3), pixels[:, -4:].reshape(-1, 3)))
    gutter_color = np.median(border, axis=0)
    return (np.linalg.norm(pixels - gutter_color, axis=2) > 20).astype(np.float32)


def measure_opaque_crop(raw, painted, cell, reference_size):
    """Find the actual painted rectangle; imagegen can compress sheet gutters."""
    x, y, width, height = cell["reference_rect"]
    x0 = round(x * raw.width / reference_size[0])
    x1 = round((x + width) * raw.width / reference_size[0])
    y0 = round(y * raw.height / reference_size[1])
    y1 = round((y + height) * raw.height / reference_size[1])

    row_profile = painted[:, x0 + 8:x1 - 8].mean(axis=1)
    top_score, top = boundary(row_profile, y0, 1, 28)
    bottom_score, bottom = boundary(row_profile, y1, -1, 28)
    column_profile = painted[top + 20:bottom - 20].mean(axis=0)
    left_score, left = boundary(column_profile, x0, 1, 20)
    right_score, right = boundary(column_profile, x1, -1, 20)
    scores = [float(value) for value in (left_score, top_score, right_score, bottom_score)]
    if min(scores) < 0.25 or not (0.85 * (x1 - x0) < right - left < 1.15 * (x1 - x0)) or not (
            0.85 * (y1 - y0) < bottom - top < 1.15 * (y1 - y0)):
        raise ValueError(f"Could not confidently measure returned NPC slot {cell['id']}: {scores}")
    return raw.crop((left, top, right, bottom)), (left, top, right, bottom), scores


def main():
    catalog = {row["id"]: row for row in read_catalog()["items"]}
    output_root = HERE / "generated_npc_candidates"
    output_root.mkdir(exist_ok=True)
    entries = []
    for sheet_dir in sorted((HERE / "missing_npc_sheets").iterdir()):
        if not sheet_dir.is_dir() or not (sheet_dir / "raw.png").is_file():
            continue
        layout_path = sheet_dir / "layout.json"
        layout = json.loads(layout_path.read_text())
        raw_path = sheet_dir / "raw.png"
        with Image.open(raw_path) as raw:
            expected_ratio = layout["reference_size"][0] / layout["reference_size"][1]
            actual_ratio = raw.width / raw.height
            if abs(actual_ratio / expected_ratio - 1) > 0.01:
                raise ValueError(f"Generated sheet changed aspect ratio: {raw_path}")
            painted = opaque_paint_mask(raw) if sheet_dir.name.startswith("opaque_") else None
            for cell in layout["cells"]:
                item = catalog[cell["id"]]
                if item["source_sha256"] != cell["source_sha256"]:
                    raise ValueError(f"Source changed: {item['id']}")
                if painted is not None:
                    crop, box, alignment_scores = measure_opaque_crop(raw, painted, cell, layout["reference_size"])
                else:
                    crop, box = crop_cell(raw, cell["reference_rect"], layout["reference_size"])
                    alignment_scores = None
                if crop.width < item["x2_size"][0] or crop.height < item["x2_size"][1]:
                    raise ValueError(f"Insufficient generated sampling: {item['id']}")
                with Image.open(HERE / item["original"]) as original:
                    candidate = fit_candidate(crop, original.convert("RGBA"), tuple(item["x2_size"]))
                target = output_root / (item["id"] + ".png")
                candidate.save(target, optimize=True)
                entries.append({
                    "id": item["id"], "source_sha256": item["source_sha256"],
                    "artifact": str(target.relative_to(ROOT)), "artifact_sha256": sha256(target),
                    "raw": str(raw_path.relative_to(ROOT)), "raw_sha256": sha256(raw_path),
                    "layout": str(layout_path.relative_to(ROOT)), "reference_rect": cell["reference_rect"],
                    "actual_crop": box, "alignment_scores": alignment_scores,
                    "status": "unverified new imagegen master extraction",
                    "source_label": "new NPC imagegen master",
                    "note": "Returned slot measured against its gutters and resized to exact 2x; identity, expression and borders need review.",
                })
    (output_root / "manifest.json").write_text(json.dumps({"schema": 1, "items": entries}, indent=2) + "\n")
    print(f"Extracted {len(entries)} NPC portraits from {len({row['raw'] for row in entries})} new sheets.")


if __name__ == "__main__":
    main()
