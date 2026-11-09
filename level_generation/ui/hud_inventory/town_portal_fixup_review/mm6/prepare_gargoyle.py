#!/usr/bin/env python3
"""Localize the final HOMM2 gargoyle correction without changing the approved map."""

import json
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image

from prepare_creature_fixup import digest, region_mask


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
OUT = HERE / "creature_fixup_v2"


def main():
    if (HERE.parents[1] / "town_portal_acceptance_20260927/accepted.json").exists():
        raise SystemExit("This revision is accepted; create a new revision before preparing new artwork.")
    OUT.mkdir(exist_ok=True)
    previous = Image.open(HERE / "creature_fixup/master.png").convert("RGB")
    generated = Image.open(HERE / "attempt_06/raw.png").convert("RGB")
    assert previous.size == generated.size == (1448, 1086)
    box = (180, 337, 276, 448)
    mask = region_mask(previous.size, box, 4)
    mask.save(OUT / "gargoyle_mask.png")
    master = OUT / "master.png"
    Image.composite(generated, previous, mask).save(master)
    export = OUT / "tpenroth.png"
    subprocess.run([
        "magick", str(master), "-filter", "Lanczos", "-resize", "1280x960",
        "-define", "png:color-type=2", str(export),
    ], check=True)
    before = np.asarray(Image.open(HERE / "creature_fixup/tpenroth.png"))
    after = np.asarray(Image.open(export))
    changed = np.any(before != after, axis=2)
    bounds = [155, 293, 249, 401]
    allowed = np.zeros(changed.shape, dtype=bool)
    allowed[bounds[1]:bounds[3], bounds[0]:bounds[2]] = True
    assert not np.any(changed & ~allowed)
    inputs = [HERE / "creature_fixup/master.png", HERE / "attempt_06/raw.png",
              HERE / "attempt_05/inputs/gargoyle.png"]
    manifest = {
        "schema": 1, "target": "engine--icons--tpenroth.bmp", "status": "review_candidate",
        "scope": "HOMM2 gargoyle, reduced and simplified to match the Titan's sepia stencil treatment",
        "accepted_in_ledger": False, "installed": False,
        "logical_size": [640, 480], "export_size": [1280, 960],
        "inputs": [{"path": str(p.relative_to(ROOT)), "sha256": digest(p)} for p in inputs],
        "patch": {"raw_box": list(box), "feather_pixels": 4, "export_change_bounds": bounds},
        "master": {"path": str(master.relative_to(ROOT)), "sha256": digest(master), "size": [1448, 1086]},
        "export": {"path": str(export.relative_to(ROOT)), "sha256": digest(export)},
        "validation": {"result": "PASS", "changed_pixels": int(changed.sum()),
                       "all_pixels_outside_gargoyle_patch_identical": True,
                       "titan_and_destination_regions_unchanged": True, "opaque_rgb": True},
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest["validation"], indent=2))


if __name__ == "__main__":
    main()
