"""Extract exact-2x review previews from the new paired spell masters."""

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

from extract_raw_buttons import crop_cell, fit_candidate, read_catalog


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    catalog = {row["id"]: row for row in read_catalog()["items"]}
    output_root = HERE / "generated_spell_candidates"
    output_root.mkdir(exist_ok=True)
    entries = []
    for sheet_dir in sorted((HERE / "missing_spell_sheets").iterdir()):
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
            for cell in layout["cells"]:
                item = catalog[cell["id"]]
                if item["source_sha256"] != cell["source_sha256"]:
                    raise ValueError(f"Source changed: {item['id']}")
                crop, box = crop_cell(raw, cell["reference_rect"], layout["reference_size"])
                if crop.width < item["x2_size"][0] or crop.height < item["x2_size"][1]:
                    raise ValueError(f"Insufficient generated sampling: {item['id']}")
                with Image.open(HERE / item["original"]) as original:
                    original = original.convert("RGBA")
                    candidate = fit_candidate(crop, original, tuple(item["x2_size"]))
                    native_mask = original.getchannel("A").resize(tuple(item["x2_size"]), Image.Resampling.NEAREST)
                    candidate.putalpha(ImageChops.multiply(candidate.getchannel("A"), native_mask))
                target = output_root / (item["id"] + ".png")
                candidate.save(target, optimize=True)
                entries.append({
                    "id": item["id"], "source_sha256": item["source_sha256"],
                    "artifact": str(target.relative_to(ROOT)), "artifact_sha256": sha256(target),
                    "raw": str(raw_path.relative_to(ROOT)), "raw_sha256": sha256(raw_path),
                    "layout": str(layout_path.relative_to(ROOT)), "reference_rect": cell["reference_rect"],
                    "actual_crop": box, "status": "unverified new imagegen master extraction",
                    "source_label": "new paired spell imagegen master",
                    "note": "Exact-2x preview with native alpha mask; paired art, placement and key edges need review.",
                })
    (output_root / "manifest.json").write_text(json.dumps({"schema": 1, "items": entries}, indent=2) + "\n")
    print(f"Extracted {len(entries)} spell states from {len({row['raw'] for row in entries})} new sheets.")


if __name__ == "__main__":
    main()
