"""Make provisional 2x previews from retained, unmapped checkpoint raw sheets.

The payload's execution layout identifies each generated slot. Extraction does
not approve the generated artwork or change the restoration checkpoint.
"""

import hashlib
import json
from pathlib import Path
import re

from PIL import Image

from extract_raw_buttons import crop_cell, fit_candidate, read_catalog


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    catalog = read_catalog()
    output_root = HERE / "provisional_checkpoint"
    output_root.mkdir(exist_ok=True)
    items = []
    failures = []
    for item in catalog["items"]:
        reviewed_candidates = [candidate for candidate in item["candidates"] if not candidate["status"].startswith("unverified")]
        if reviewed_candidates or not item["raw_master"]:
            continue
        raw = (HERE / item["raw_master"]).resolve()
        match = re.search(r"/checkpoint/attempts/([0-9a-f]{32})/raw\.png$", str(raw))
        if not match:
            continue
        payload_path = raw.parent / "payload.json"
        if not payload_path.is_file():
            failures.append({"id": item["id"], "reason": "Missing payload"})
            continue
        payload = json.loads(payload_path.read_text())
        layout = payload.get("execution_layout") or {}
        rect = layout.get("cell_rects", {}).get(item["id"])
        if not rect:
            failures.append({"id": item["id"], "reason": "No execution rectangle"})
            continue
        source_hash = payload.get("source_hashes", {}).get(item["id"])
        if source_hash and source_hash != item["source_sha256"]:
            failures.append({"id": item["id"], "reason": "Source hash changed"})
            continue
        with Image.open(raw) as sheet_image, Image.open(HERE / item["original"]) as original_image:
            crop, actual_box = crop_cell(sheet_image, rect, layout["canvas_size"])
            if crop.width < item["x2_size"][0] or crop.height < item["x2_size"][1]:
                failures.append({"id": item["id"], "reason": "Less than 2x raw sampling"})
                continue
            restored = fit_candidate(crop, original_image.convert("RGBA"), tuple(item["x2_size"]))
            target = output_root / (item["id"] + ".png")
            restored.save(target, optimize=True)
        items.append({
            "id": item["id"], "artifact": str(target.relative_to(ROOT)), "artifact_sha256": sha256(target),
            "source_sha256": item["source_sha256"], "raw": str(raw.relative_to(ROOT)),
            "raw_sha256": sha256(raw), "payload": str(payload_path.relative_to(ROOT)),
            "reference_rect": rect, "actual_crop": actual_box,
            "status": "unverified checkpoint-sheet extraction",
            "note": "Execution slot scaled to native 2x canvas; visual identity, fitting, compositing and animation need review.",
        })
    manifest = {"schema": 1, "items": items, "failures": failures}
    (output_root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Extracted {len(items)} provisional checkpoint candidates; {len(failures)} could not be extracted.")
    for failure in failures[:20]:
        print(f"  {failure['id']}: {failure['reason']}")


if __name__ == "__main__":
    main()
