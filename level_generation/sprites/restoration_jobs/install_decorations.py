#!/usr/bin/env python3
"""Install accepted 2x decoration canvases without changing the native sprites."""

import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[3]
JOBS = Path(__file__).resolve().parent
DESTINATION = ROOT / "assets_dev/engine/decorations_x2"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    existing_manifest = DESTINATION / "manifest.json"
    if existing_manifest.exists():
        installed = json.loads(existing_manifest.read_text())
        if installed.get("source") != "level_generation/sprites/restoration_jobs/export.json":
            raise ValueError("This pack uses an approved review overlay; use runs/remaining_review_20260923/install_approved.py")
    groups = json.loads((JOBS / "groups.json").read_text())
    export = json.loads((JOBS / "export.json").read_text())
    if export["status"] != "complete" or export["pixels_per_logical_pixel"] != 2:
        raise ValueError("Decoration export must be complete at 2x")

    asset_ids = {asset for group in groups if group["category"] == "decorations" for asset in group["assets"]}
    frames = export["frames"]
    if not asset_ids <= frames.keys():
        raise ValueError(f"Missing accepted decoration canvases: {sorted(asset_ids - frames.keys())}")

    bindings = {}
    for asset_id in sorted(asset_ids):
        frame = frames[asset_id]
        source = ROOT / frame["file"]
        if sha256(source) != frame["sha256"]:
            raise ValueError(f"Export hash mismatch: {source}")
        with Image.open(source) as image:
            if image.mode != "RGBA" or list(image.size) != frame["physical_size"]:
                raise ValueError(f"Invalid RGBA canvas: {source}")
        if frame["physical_size"] != [size * 2 for size in frame["logical_size"]]:
            raise ValueError(f"Incorrect logical size: {source}")
        for alias in frame["aliases"]:
            original = ROOT / alias["path"]
            if sha256(original) != alias["sha256"]:
                raise ValueError(f"Native source changed: {original}")
            with Image.open(original) as image:
                if list(image.size) != frame["logical_size"]:
                    raise ValueError(f"Native canvas size changed: {original}")
            name = alias["name"].lower()
            palette_id = alias["palette_id"]
            if not name or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789_.-" for character in name):
                raise ValueError(f"Invalid sprite name: {name}")
            key = (name, palette_id)
            previous = bindings.setdefault(key, (asset_id, frame))
            if previous[0] != asset_id:
                raise ValueError(f"Conflicting restored appearances: {key}")

    DESTINATION.mkdir(parents=True, exist_ok=True)
    entries = []
    for (name, palette_id), (asset_id, frame) in sorted(bindings.items()):
        filename = f"{name}_p{palette_id}.png"
        target = DESTINATION / filename
        if not target.exists() or sha256(target) != frame["sha256"]:
            shutil.copyfile(ROOT / frame["file"], target)
        entries.append({
            "name": name,
            "palette_id": palette_id,
            "file": filename,
            "asset": asset_id,
            "sha256": frame["sha256"],
            "logical_size": frame["logical_size"],
        })
    (DESTINATION / "manifest.json").write_text(json.dumps({
        "schema_version": 1,
        "pixels_per_logical_pixel": 2,
        "source": "level_generation/sprites/restoration_jobs/export.json",
        "bindings": entries,
    }, indent=2) + "\n")
    print(f"Installed {len(asset_ids)} decoration images as {len(entries)} name/palette bindings in {DESTINATION}")


if __name__ == "__main__":
    main()
