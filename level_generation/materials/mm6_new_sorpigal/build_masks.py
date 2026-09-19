#!/usr/bin/env python3
"""Compile numeric material masks from inspected, texture-aligned semantic regions.

These are render data, not replacement diffuse artwork. Region coordinates use the
x2 source texture's pixels. Keep the authored source immutable; export RGBA where
R = smoothness selection, G = wetness exposure, B = emissive selection, A = 255.
"""

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[3]
DESTINATION = ROOT / "assets_dev/worlds/mm6/rendering/material_masks"
SOURCE = Path(__file__).with_name("regions.json")


def compile_mask(name, definition):
    source = ROOT / definition["source"]
    with Image.open(source) as image:
        diffuse = np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0
        size = image.size
    mask = np.empty((size[1], size[0], 4), dtype=np.float32)
    mask[:] = [*definition["base"], 1.0]
    luminance = diffuse @ np.array([0.2126, 0.7152, 0.0722])

    for region in definition.get("regions", []):
        coverage = Image.new("L", size, 0)
        draw = ImageDraw.Draw(coverage)
        if "rect" in region:
            draw.rectangle(region["rect"], fill=255)
        else:
            draw.polygon([tuple(point) for point in region["polygon"]], fill=255)
        selected = np.asarray(coverage) > 0
        # Keep painted lead cames, deep cracks, and recessed joints out of polished areas.
        if "minimum_luminance" in region:
            selected &= luminance > region["minimum_luminance"]
        if "minimum_red_difference" in region:
            selected &= diffuse[:, :, 0] - diffuse[:, :, 1] > region["minimum_red_difference"]
        for channel, value in enumerate(region["channels"]):
            mask[:, :, channel][selected] = value

    output = DESTINATION / f"{name}.png"
    Image.fromarray(np.rint(np.clip(mask, 0.0, 1.0) * 255).astype(np.uint8)).save(output)
    output.chmod(0o644)
    return {
        "source": definition["source"],
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "output": str(output.relative_to(ROOT)),
        "size": list(size),
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "purpose": definition["purpose"],
    }


def main():
    definitions = json.loads(SOURCE.read_text())
    DESTINATION.mkdir(parents=True, exist_ok=True)
    manifest = {name: compile_mask(name, definition) for name, definition in definitions.items()}
    Path(__file__).with_name("manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Compiled {len(manifest)} material masks into {DESTINATION.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
