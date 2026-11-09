"""Record the user's loading-screen and NPC portrait visual approvals.

This binds review decisions to the selected exact-2x PNG and native source
hashes. It does not change the restoration checkpoint or runtime packages.
"""

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from extract_raw_buttons import read_catalog


HERE = Path(__file__).resolve().parent
CATEGORIES = ("Loading screens", "NPC portraits")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def purple_profile(image):
    rgba = np.asarray(image.convert("RGBA"))
    red, green, blue = np.moveaxis(rgba[:, :, :3].astype(np.float32), 2, 0)
    purple = ((red > 70) & (blue > 70) & (red > green * 1.35)
              & (blue > green * 1.35) & (rgba[:, :, 3] >= 16))
    outer = purple
    inner = purple[1:-1, 1:-1]
    return [int(ring[0].sum() + ring[-1].sum() + ring[:, 0].sum() + ring[:, -1].sum())
            for ring in (outer, inner)]


def loading_outer_purple(image):
    rgba = np.asarray(image.convert("RGBA"))
    red, green, blue = np.moveaxis(rgba[:, :, :3].astype(np.float32), 2, 0)
    purple = ((red > 70) & (blue > 70) & (red > green * 1.35)
              & (blue > green * 1.35) & (rgba[:, :, 3] >= 16))
    purple[3:-3, 3:-3] = False
    return int(purple.sum())


def loading_key_pixels(image):
    rgba = np.asarray(image.convert("RGBA"))
    red, green, blue = np.moveaxis(rgba[:, :, :3].astype(np.int16), 2, 0)
    key = ((red >= 150) & (blue >= 150) & (green <= 90)
           & (abs(red - blue) <= 110) & (rgba[:, :, 3] > 0))
    return int(key.sum())


def main():
    catalog = read_catalog()
    candidates = [item for item in catalog["items"] if item["category"] in CATEGORIES]
    if len(candidates) != 1760:
        raise ValueError(f"Expected 17 loading assets and 1,743 NPC portraits, got {len(candidates)}")
    cleanup = json.loads((HERE / "cleaned_npc_edges/manifest.json").read_text())
    if cleanup["unresolved"]:
        raise ValueError("NPC magenta edge review is still unresolved")

    entries = []
    for item in candidates:
        if not item["candidates"]:
            raise ValueError(f"Missing 2x candidate: {item['id']}")
        candidate = item["candidates"][0]
        if sha256(HERE / item["source"]) != item["source_sha256"]:
            raise ValueError(f"Native source changed: {item['id']}")
        if sha256(HERE / candidate["path"]) != candidate["sha256"]:
            raise ValueError(f"Candidate changed: {item['id']}")
        with Image.open(HERE / candidate["path"]) as source:
            art = source.convert("RGBA")
        if art.size != tuple(item["x2_size"]):
            raise ValueError(f"Candidate is not exact 2x: {item['id']}")
        if item["category"] == "Loading screens":
            if loading_outer_purple(art):
                raise ValueError(f"Purple loading-screen edge: {item['id']}")
            if loading_key_pixels(art):
                raise ValueError(f"Magenta key pixel in loading art: {item['id']}")
        else:
            with Image.open(HERE / item["original"]) as source:
                native = source.convert("RGBA").resize(art.size, Image.Resampling.NEAREST)
            candidate_edge = purple_profile(art)
            native_edge = purple_profile(native)
            frame = (candidate_edge[0] >= 20
                     and candidate_edge[0] >= candidate_edge[1] * 3 + 15
                     and candidate_edge[0] >= native_edge[0] + 15)
            if frame:
                raise ValueError(f"Purple one-pixel NPC frame: {item['id']}")
        entries.append({
            "id": item["id"], "category": item["category"],
            "source_sha256": item["source_sha256"],
            "candidate_sha256": candidate["sha256"],
            "artifact": candidate["path"],
            "decision": "approve",
        })
    revision = hashlib.sha256(json.dumps(entries, sort_keys=True).encode()).hexdigest()[:16]
    manifest = {
        "schema": 1,
        "kind": "visual_review_acceptance",
        "revision": revision,
        "scope": list(CATEGORIES),
        "audit": {
            "loading_outer_purple_pixels": 0,
            "loading_magenta_key_pixels": 0,
            "npc_rectangular_frame_signatures": 0,
            "mechanically_cleaned_npc_candidates": len(cleanup["items"]),
            "manual_native_color_checks": [
                "npc0320", "npc0707", "npc0747", "npc0925",
                "npc1201", "npc1290", "npc1345", "npc1499",
            ],
        },
        "items": entries,
    }
    (HERE / "review_acceptance.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Recorded {len(entries)} visual approvals at revision {revision}")


if __name__ == "__main__":
    main()
