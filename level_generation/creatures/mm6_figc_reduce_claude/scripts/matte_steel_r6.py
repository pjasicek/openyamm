#!/usr/bin/env python3
"""Codex round-6 mid-grey matte steel (../mm6_figc_codex/scripts/materials_r6.py) on a reduced figc prop.

    matte_steel_r6.py <in.glb> <out.glb> <ramp source.glb>

Every material's steel ramp (region 2, the mask's blue channel) takes the colours of the ramp source's first material
(the round-6 axe: one gear steel ramp for all tiers), and the metal-rough texture gets the round-6 steel response:
specular mask (red) capped at 32/255 and roughness (green) raised to at least 220/255, blended by the steel mask.
Geometry, UVs, base colour, normal and mask images are unchanged; the binary chunk is rebuilt without the old image.
"""
import io
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "tools"))
from build_actor_lods import read_glb, write_glb  # noqa: E402


def imageBytes(document, binary, index):
    view = document["bufferViews"][document["images"][index]["bufferView"]]
    start = view.get("byteOffset", 0)
    return binary[start:start + view["byteLength"]]


def main():
    source, output, rampSource = (Path(arg) for arg in sys.argv[1:4])
    document, binary = read_glb(source)
    rampDocument, _ = read_glb(rampSource)
    steel = rampDocument["materials"][0]["extras"]["openyamm_region_ramps"][2]

    roughnessImages = set()
    for material in document["materials"]:
        ramps = material["extras"]["openyamm_region_ramps"]
        if ramps[2]["range"] != steel["range"]:
            raise SystemExit(f"{material['name']}: steel ramp range {ramps[2]['range']} != {steel['range']}")
        ramps[2]["colors"] = steel["colors"]
        textures = document["textures"]
        roughness = textures[material["pbrMetallicRoughness"]["metallicRoughnessTexture"]["index"]]["source"]
        mask = textures[material["extras"]["openyamm_region_mask"]["index"]]["source"]
        roughnessImages.add((roughness, mask))
    if len(roughnessImages) != 1:
        raise SystemExit(f"expected one shared metal-rough and mask image, got {roughnessImages}")
    roughness, mask = roughnessImages.pop()

    mr = np.array(Image.open(io.BytesIO(imageBytes(document, binary, roughness))).convert("RGB")).astype(float)
    weight = np.array(Image.open(io.BytesIO(imageBytes(document, binary, mask))).convert("RGBA"))[:, :, 2] / 255
    mr[:, :, 0] = np.rint(mr[:, :, 0] * (1 - weight) + np.minimum(mr[:, :, 0], 32) * weight)
    mr[:, :, 1] = np.rint(mr[:, :, 1] * (1 - weight) + np.maximum(mr[:, :, 1], 220) * weight)
    encoded = io.BytesIO()
    Image.fromarray(mr.astype(np.uint8)).save(encoded, format="PNG", optimize=True)

    # Rebuild the binary chunk: every buffer view in order, the metal-rough image's view replaced.
    replaced = document["images"][roughness]["bufferView"]
    compact = bytearray()
    for index, view in enumerate(document["bufferViews"]):
        data = encoded.getvalue() if index == replaced else bytes(binary[view.get("byteOffset", 0):
                                                                         view.get("byteOffset", 0) + view["byteLength"]])
        compact += b"\0" * (-len(compact) % 4)
        view["byteOffset"] = len(compact)
        view["byteLength"] = len(data)
        compact += data
    document["images"][roughness]["name"] = document["images"][roughness].get("name", "") + "_matte_steel"
    write_glb(output, document, bytes(compact))
    print(f"{output.name}: {len(document['materials'])} materials, steel ramp top {steel['colors'][-1]}, "
          f"metal-rough {mr.shape[1]}x{mr.shape[0]} matte in {weight.mean():.1%} of texels")


if __name__ == "__main__":
    main()
