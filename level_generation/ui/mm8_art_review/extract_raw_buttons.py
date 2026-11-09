"""Extract provisional button comparisons from retained dense imagegen sheets.

The returned sheet is already generated artwork. This makes exact-2x comparison
PNGs; it does not claim that nominal sheet slots pass registration or art review.
"""

import hashlib
import json
from pathlib import Path
import re

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HUD = ROOT / "level_generation/ui/hud_inventory"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_catalog():
    source = (HERE / "catalog.js").read_text()
    return json.loads(source.removeprefix("window.REVIEW_CATALOG = ").removesuffix(";\n"))


def source_matte(image):
    pixels = np.array(image.convert("RGB"))
    matte = ((pixels[:, :, 0] >= 180) & (pixels[:, :, 1] <= 80)
             & (pixels[:, :, 2] >= 180))
    return matte


def crop_cell(image, rect, reference_size):
    scale_x = image.width / reference_size[0]
    scale_y = image.height / reference_size[1]
    x, y, width, height = rect
    box = (round(x * scale_x), round(y * scale_y),
           round((x + width) * scale_x), round((y + height) * scale_y))
    return image.crop(box), box


def fit_candidate(crop, original, size):
    rgba = np.array(crop.convert("RGBA"))
    # A returned RGBA sheet already carries its own matte. Only key the
    # magenta background on flattened RGB sheets.
    has_alpha = "A" in crop.getbands() and crop.getchannel("A").getextrema() != (255, 255)
    matte = np.zeros((crop.height, crop.width), dtype=bool) if has_alpha else source_matte(crop)
    opaque_original = original.getchannel("A").getextrema() == (255, 255)
    if opaque_original:
        # Full-canvas buttons may have one or two sheet-matte pixels outside the panel.
        visible = Image.fromarray((~matte).astype(np.uint8) * 255)
        bounds = visible.getbbox()
        if bounds and bounds[2] - bounds[0] >= crop.width * 0.75 and bounds[3] - bounds[1] >= crop.height * 0.75:
            if bounds[2] - bounds[0] > 100 and bounds[3] - bounds[1] > 40:
                bounds = (bounds[0] + 2, bounds[1] + 2, bounds[2] - 2, bounds[3] - 2)
            rgba = rgba[bounds[1]:bounds[3], bounds[0]:bounds[2]]
        restored = Image.fromarray(rgba, "RGBA").resize(size, Image.Resampling.LANCZOS)
        restored.putalpha(Image.new("L", size, 255))
        return restored

    rgba[matte, 3] = 0
    rgba[matte, :3] = 0
    restored = Image.fromarray(rgba, "RGBA").resize(size, Image.Resampling.LANCZOS)
    source_bounds = original.getchannel("A").resize(size, Image.Resampling.NEAREST).getbbox()
    result_bounds = restored.getchannel("A").getbbox()
    if source_bounds and result_bounds:
        offset_x = source_bounds[0] - result_bounds[0]
        offset_y = source_bounds[1] - result_bounds[1]
        if abs(offset_x) <= 16 and abs(offset_y) <= 16:
            canvas = Image.new("RGBA", size)
            canvas.paste(restored, (offset_x, offset_y))
            restored = canvas
    return restored


def main():
    catalog = read_catalog()
    output_root = HERE / "provisional_raw_buttons"
    output_root.mkdir(exist_ok=True)
    items = []
    failures = []
    for item in catalog["items"]:
        reviewed_candidates = [candidate for candidate in item["candidates"]
                               if candidate["status"] != "unverified raw-sheet extraction"]
        if item["category"] != "UI buttons" or reviewed_candidates or not item["raw_master"]:
            continue
        raw = (HERE / item["raw_master"]).resolve()
        match = re.search(r"/dense_returns/(dense64_[^/]+)-[0-9a-f]{12}/incoming/outputs/raw/(S\d+)\.png$", str(raw))
        if not match:
            failures.append({"id": item["id"], "reason": "Raw source is not a dense sheet"})
            continue
        bundle, sheet = match.groups()
        layout_path = HUD / "chat_bundles/dense64_20260916" / bundle / "sheets" / sheet / "layout.json"
        if not layout_path.is_file():
            failures.append({"id": item["id"], "reason": "Missing frozen sheet layout"})
            continue
        layout = json.loads(layout_path.read_text())
        cell = next((entry for entry in layout["cells"] if entry["id"] == item["id"]), None)
        if cell is None:
            failures.append({"id": item["id"], "reason": "Missing cell in frozen layout"})
            continue
        if cell["source_sha256"] != item["source_sha256"]:
            failures.append({"id": item["id"], "reason": "Source hash changed"})
            continue
        with Image.open(raw) as sheet_image, Image.open(HERE / item["original"]) as original_image:
            crop, actual_box = crop_cell(sheet_image, cell["reference_rect"], layout["reference_size"])
            if crop.width < item["x2_size"][0] or crop.height < item["x2_size"][1]:
                failures.append({"id": item["id"], "reason": "Less than 2x raw sampling"})
                continue
            restored = fit_candidate(crop, original_image.convert("RGBA"), tuple(item["x2_size"]))
            target = output_root / (item["id"] + ".png")
            restored.save(target, optimize=True)
        items.append({
            "id": item["id"], "artifact": str(target.relative_to(ROOT)), "artifact_sha256": sha256(target),
            "source_sha256": item["source_sha256"], "raw": str(raw.relative_to(ROOT)),
            "raw_sha256": sha256(raw), "layout": str(layout_path.relative_to(ROOT)),
            "reference_rect": cell["reference_rect"], "actual_crop": actual_box,
            "status": "unverified raw-sheet extraction",
            "note": "Nominal sheet slot; visual identity, fitting, text and alpha need individual review.",
        })
    manifest = {"schema": 1, "items": items, "failures": failures}
    (output_root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Extracted {len(items)} provisional button candidates; {len(failures)} could not be extracted.")
    for failure in failures[:20]:
        print(f"  {failure['id']}: {failure['reason']}")


if __name__ == "__main__":
    main()
