"""Make review-only NPC previews with obvious sheet-matte borders removed.

The untouched 2x candidate remains available as a browser variant. A border is
changed when a thin purple band is stronger than both the native edge and the
candidate's neighboring pixels. Genuine purple inside the art is retained.
"""

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from extract_raw_buttons import read_catalog


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def purple_profile(image, minimum=60):
    rgb = np.asarray(image.convert("RGB"), dtype=np.float32)
    red, green, blue = np.moveaxis(rgb, 2, 0)
    purple = (red > green * 1.35) & (blue > green * 1.35) & (red > minimum) & (blue > minimum)
    counts = []
    for distance in range(5):
        ring = purple[distance:purple.shape[0] - distance,
                      distance:purple.shape[1] - distance]
        counts.append(int(ring[0].sum() + ring[-1].sum() + ring[1:-1, 0].sum()
                          + ring[1:-1, -1].sum()))
    return counts


def clean_border(image, depth):
    pixels = np.asarray(image.convert("RGBA"))
    height, width = pixels.shape[:2]
    y = np.clip(np.arange(height), depth, height - depth - 1)
    x = np.clip(np.arange(width), depth, width - depth - 1)
    return Image.fromarray(pixels[y[:, None], x[None, :]], "RGBA")


def main():
    output_dir = HERE / "cleaned_npc_edges"
    output_dir.mkdir(exist_ok=True)
    entries = []
    unresolved = []
    for item in read_catalog()["items"]:
        if item["category"] != "NPC portraits":
            continue
        base = next((candidate for candidate in item["candidates"]
                     if candidate["source"] != "review-only border repair"), None)
        if base is None or base["status"] == "pipeline accepted":
            continue
        base_path = (HERE / base["path"]).resolve()
        with Image.open(HERE / item["original"]) as native, Image.open(base_path) as candidate:
            if native.convert("RGBA").getchannel("A").getextrema() != (255, 255):
                continue
            native_x2 = native.resize(tuple(item["x2_size"]), Image.Resampling.NEAREST)
            original_profile = purple_profile(native_x2)
            candidate_profile = purple_profile(candidate)
            original_fringe = purple_profile(native_x2, 70)
            candidate_fringe = purple_profile(candidate, 70)
            isolated_matte = candidate_profile[0] >= 50 and original_profile[0] < 10
            depth = next((distance for distance in range(1, 4)
                          if isolated_matte and candidate_profile[distance] <= 10
                          and all(count >= 10 for count in candidate_profile[:distance])), None)
            residual_matte = (
                (candidate_profile[0] >= 20
                 and candidate_profile[0] >= original_profile[0] + 15
                 and candidate_profile[0] >= candidate_profile[1] * 3 + 15)
                or (candidate_fringe[0] >= 20
                    and candidate_fringe[0] >= original_fringe[0] + 15
                    and candidate_fringe[0] >= candidate_fringe[1] * 3 + 15)
            )
            if depth is None and (isolated_matte or residual_matte):
                # The first pixel is a matte frame even when legitimate purple continues farther inward.
                depth = 1
            if depth is None:
                continue
            cleaned = clean_border(candidate, depth)
            output = output_dir / (item["id"] + ".png")
            cleaned.save(output, optimize=True)
            cleaned_profile = purple_profile(cleaned)
            if isolated_matte and candidate_profile[depth] <= 10 and cleaned_profile[0] > 10:
                raise ValueError(f"Border cleanup did not remove the isolated matte: {item['id']}")
            if cleaned_profile[0] >= candidate_profile[0] * 0.75:
                raise ValueError(f"Border cleanup did not reduce the matte: {item['id']}")
        entries.append({
            "id": item["id"], "source_sha256": item["source_sha256"],
            "artifact": str(output.relative_to(ROOT)), "artifact_sha256": sha256(output),
            "parent_artifact": str(base_path.relative_to(ROOT)),
            "parent_artifact_sha256": sha256(base_path),
            "border_depth": depth, "candidate_profile": candidate_profile,
            "original_profile": original_profile, "cleaned_profile": cleaned_profile,
            "status": "unverified mechanical edge cleanup",
            "source_label": "review-only border repair",
            "note": "Only the outer 1-3 pixels were replaced from adjacent interior pixels; compare the untouched variant.",
        })
    (output_dir / "manifest.json").write_text(json.dumps({
        "schema": 1, "items": entries, "unresolved": unresolved,
    }, indent=2) + "\n")
    print(f"Cleaned {len(entries)} isolated NPC borders; {len(unresolved)} need visual edge review.")


if __name__ == "__main__":
    main()
