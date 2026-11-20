"""Extract review-only council body repairs from identity-edit sheets.

The generated sheets are composition references. The earlier candidate's alpha
and outer two pixels remain authoritative for each exact-size cutout.
"""

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = HERE / "council_body_repair"
TARGETS = ROOT / "level_generation/ui/hud_inventory/expected_targets.json"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def extract_cell(sheet, cell):
    x, y, width, height = cell["sheet_rect"]
    source = sheet.crop((x, y, x + width, y + height))
    return source.resize(tuple(cell["x2_size"]), Image.Resampling.LANCZOS)


def preserve_cutout(generated, parent):
    parent_alpha = parent.getchannel("A")
    inner = parent_alpha.filter(ImageFilter.MinFilter(5))
    generated_alpha = generated.getchannel("A").point(lambda value: 255 if value >= 180 else 0)
    edit_mask = ImageChops.multiply(inner, generated_alpha)
    repaired = Image.composite(generated.convert("RGB"), parent.convert("RGB"), edit_mask).convert("RGBA")
    repaired.putalpha(parent_alpha)
    return repaired


def main():
    targets = {row["id"]: row for row in json.loads(TARGETS.read_text())["targets"]}
    entries = []
    out_dir = BASE / "candidates"
    out_dir.mkdir(parents=True, exist_ok=True)
    for directory in sorted(BASE.iterdir()):
        if not directory.is_dir() or not (directory / "layout.json").is_file():
            continue
        layout_path = directory / "layout.json"
        layout = json.loads(layout_path.read_text())
        raw_path = directory / "raw.png"
        with Image.open(raw_path) as image:
            if image.width * layout["sheet_size"][1] != image.height * layout["sheet_size"][0]:
                raise ValueError(f"Unexpected sheet aspect ratio: {raw_path}")
            sheet = image.convert("RGBA").resize(tuple(layout["sheet_size"]), Image.Resampling.LANCZOS)
        raw_sha = sha256(raw_path)
        for cell in layout["cells"]:
            target = targets[cell["id"]]
            native_path = ROOT / target["source_path"]
            parent_path = ROOT / cell["parent_artifact"]
            if sha256(native_path) != cell["source_sha256"] or target["source_sha256"] != cell["source_sha256"]:
                raise ValueError(f"Native source changed: {cell['id']}")
            if sha256(parent_path) != cell["parent_sha256"]:
                raise ValueError(f"Parent candidate changed: {cell['id']}")
            with Image.open(parent_path) as image:
                parent = image.convert("RGBA")
            if parent.size != tuple(cell["x2_size"]):
                raise ValueError(f"Parent size changed: {cell['id']}")
            generated = extract_cell(sheet, cell)
            repaired = preserve_cutout(generated, parent)
            artifact = out_dir / f"{cell['id']}.png"
            repaired.save(artifact, optimize=True)
            if repaired.getchannel("A").tobytes() != parent.getchannel("A").tobytes():
                raise ValueError(f"Cutout alpha changed: {cell['id']}")
            entries.append({
                "id": cell["id"],
                "source_sha256": cell["source_sha256"],
                "artifact": relative(artifact),
                "artifact_sha256": sha256(artifact),
                "parent_artifact": cell["parent_artifact"],
                "parent_artifact_sha256": cell["parent_sha256"],
                "raw": relative(raw_path),
                "raw_sha256": raw_sha,
                "intermediate_raw": relative(directory / "raw_v1.png")
                    if (directory / "raw_v1.png").is_file() else None,
                "refinement_prompt": relative(directory / "refinement_prompt.txt")
                    if (directory / "refinement_prompt.txt").is_file() else None,
                "layout": relative(layout_path),
                "reference_avatar_id": layout["avatar"],
                "reference_avatar_sha256": layout["avatar_sha256"],
                "reference_avatar_candidate_sha256": layout["avatar_candidate_sha256"],
                "status": "unverified council identity repair",
                "source_label": "avatar-matched council body repair",
            })
            print(cell["name"], artifact, repaired.size)
    if len(entries) != 11:
        raise ValueError(f"Expected 11 repaired bodies, got {len(entries)}")
    (BASE / "manifest.json").write_text(json.dumps({"schema": 1, "items": entries}, indent=2) + "\n")


if __name__ == "__main__":
    main()
