"""Remove isolated, nearly transparent magenta key pixels from loading frames."""

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from extract_raw_buttons import read_catalog


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUTPUT = HERE / "cleaned_loading_key_pixels"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUTPUT.mkdir(exist_ok=True)
    entries = []
    total_pixels = 0
    for item in read_catalog()["items"]:
        if item["category"] != "Loading screens":
            continue
        parent = next(candidate for candidate in item["candidates"]
                      if candidate["source"] != "review-only transparent key cleanup")
        parent_path = (HERE / parent["path"]).resolve()
        with Image.open(parent_path) as source:
            pixels = np.array(source.convert("RGBA"))
        red, green, blue = np.moveaxis(pixels[:, :, :3].astype(np.int16), 2, 0)
        key = ((red >= 150) & (blue >= 150) & (green <= 90)
               & (abs(red - blue) <= 110) & (pixels[:, :, 3] <= 3))
        count = int(key.sum())
        if not count:
            continue
        pixels[key] = [0, 0, 0, 0]
        artifact = OUTPUT / f"{item['id']}.png"
        Image.fromarray(pixels, "RGBA").save(artifact, optimize=True)
        entries.append({
            "id": item["id"], "source_sha256": item["source_sha256"],
            "artifact": artifact.relative_to(ROOT).as_posix(),
            "artifact_sha256": sha256(artifact),
            "parent_artifact": parent_path.relative_to(ROOT).as_posix(),
            "parent_artifact_sha256": sha256(parent_path),
            "pixels_cleared": count,
            "status": "unverified mechanical key cleanup",
            "source_label": "review-only transparent key cleanup",
        })
        total_pixels += count
    if total_pixels != 7:
        raise ValueError(f"Expected seven isolated key pixels, got {total_pixels}")
    (OUTPUT / "manifest.json").write_text(json.dumps({"schema": 1, "items": entries}, indent=2) + "\n")
    print(f"Cleared {total_pixels} nearly transparent magenta pixels in {len(entries)} loading frames")


if __name__ == "__main__":
    main()
