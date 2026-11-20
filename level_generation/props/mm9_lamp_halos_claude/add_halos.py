#!/usr/bin/env python3
"""
A soft warm halo round the flame of MM9's street lamps and lanterns (user, 2026-11-04: "only drawing the flame
flipbook without any additional lighting seems wrong"; MM9 draws its CandleProp flame as a large additive sprite that
glows round the lantern, day and night). Each model gets one more primitive per LOD mesh: a camera-facing square card
centred on its flame cards (material `Fire`), RADIUS_PER_FLAME x the flame card's height, with the MM8 lantern's
`Halo` material as it is (level_generation/decorations/mm8_3d/animated/scripts/anim_lib.py `halo_material`: blended,
unlit, additive, `openyamm_billboard`, a flickering warm emission; the soft radial `halo` texture; COLOR_0 warm).
Additive cards also draw into the bloom view (engine/render/ModelRenderer.cpp, GlowAdditiveCardWeight).

Cost: one quad per lamp, instanced with the lamp; with bloom one more draw of it into the glow view.

    python3 level_generation/props/mm9_lamp_halos_claude/add_halos.py            # writes work/<model>.glb
    python3 level_generation/props/mm9_lamp_halos_claude/add_halos.py --install  # and installs them (--engine)

Reads the installed source GLBs (assets_source/engine/models), so a later skin install (mm9_skins_x4/skins.py, which
also starts from those) keeps the halos; a model that already has a `Halo` material is left alone.
"""

from __future__ import annotations

import argparse
import json
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MODELS = ROOT / "assets_source/engine/models"
MM8_LANTERN = MODELS / "mm8_deco_lantern.glb"
HALO_TEXTURE = ROOT / "level_generation/decorations/mm8_3d/animated/textures/halo_basecolor.png"
TARGETS = ["lamppost1", "lamppost2", "lamppost3", "lamppost4", "lantern2", "lanternwall1"]
# Halo radius in flame-card heights: the halo spans the lantern head (MM9's flame sprite reaches past the frame).
RADIUS_PER_FLAME = 1.6
WINDING = ROOT / "level_generation/decorations/mm8_3d/animated/scripts/check_winding.py"


def read_glb(path: Path):
    data = path.read_bytes()
    json_length = struct.unpack("<I", data[12:16])[0]
    gltf = json.loads(data[20:20 + json_length])
    offset = 20 + json_length
    bin_length = struct.unpack("<I", data[offset:offset + 4])[0]
    return gltf, bytearray(data[offset + 8:offset + 8 + bin_length])


def write_glb(path: Path, gltf: dict, binary: bytearray) -> None:
    text = json.dumps(gltf, separators=(",", ":")).encode()
    text += b" " * (-len(text) % 4)
    binary = bytes(binary) + b"\0" * (-len(binary) % 4)
    gltf["buffers"][0]["byteLength"] = len(binary)
    text = json.dumps(gltf, separators=(",", ":")).encode()
    text += b" " * (-len(text) % 4)
    body = struct.pack("<II", len(text), 0x4E4F534A) + text + struct.pack("<II", len(binary), 0x004E4942) + binary
    path.write_bytes(struct.pack("<III", 0x46546C67, 2, 12 + len(body)) + body)


def add_view(gltf: dict, binary: bytearray, payload: bytes, target: int | None = None) -> int:
    binary.extend(b"\0" * (-len(binary) % 4))
    view = {"buffer": 0, "byteOffset": len(binary), "byteLength": len(payload)}
    if target is not None:
        view["target"] = target
    binary.extend(payload)
    gltf["bufferViews"].append(view)
    return len(gltf["bufferViews"]) - 1


def add_accessor(gltf: dict, binary: bytearray, array: np.ndarray, kind: str, component: int, target: int,
                 bounds: bool = False, normalized: bool = False) -> int:
    accessor = {"bufferView": add_view(gltf, binary, array.tobytes(), target), "componentType": component,
                "count": int(array.shape[0]), "type": kind}
    if bounds:
        accessor["min"] = array.min(0).tolist()
        accessor["max"] = array.max(0).tolist()
    if normalized:
        accessor["normalized"] = True
    gltf["accessors"].append(accessor)
    return len(gltf["accessors"]) - 1


def mm8_halo() -> tuple[dict, list]:
    """The MM8 lantern's Halo material and its halo card's COLOR_0 (first vertex, as floats 0..1)."""
    gltf, binary = read_glb(MM8_LANTERN)
    index = next(i for i, m in enumerate(gltf["materials"]) if m["name"] == "Halo")
    material = json.loads(json.dumps(gltf["materials"][index]))
    primitive = next(p for m in gltf["meshes"] for p in m["primitives"] if p["material"] == index)
    accessor = gltf["accessors"][primitive["attributes"]["COLOR_0"]]
    view = gltf["bufferViews"][accessor["bufferView"]]
    start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    components = {"VEC3": 3, "VEC4": 4}[accessor["type"]]
    if accessor["componentType"] == 5126:
        colour = list(struct.unpack_from(f"<{components}f", binary, start))
    else:
        scale = {5121: 255.0, 5123: 65535.0}[accessor["componentType"]]
        fmt = {5121: "B", 5123: "H"}[accessor["componentType"]]
        colour = [v / scale for v in struct.unpack_from(f"<{components}{fmt}", binary, start)]
    return material, (colour + [1.0])[:4]


def add_halo(name: str, halo_material: dict, halo_colour: list) -> Path | None:
    source = MODELS / f"mm9_deco_{name}.glb"
    gltf, binary = read_glb(source)
    existing = [m for m in gltf["materials"] if m.get("name") == "Halo"]
    if existing:
        if existing[0].get("extras", {}).get("openyamm_billboard") == "card":
            print(f"{name}: already has a halo")
            return None
        # The first halos (2026-11-04) kept the MM8 lantern's whole-mesh billboard, which swung an off-centre halo
        # round the lamp's own axis (beside the post, not on the lantern): turn them about their own centre.
        existing[0].setdefault("extras", {})["openyamm_billboard"] = "card"
        out = HERE / "work" / source.name
        out.parent.mkdir(exist_ok=True)
        write_glb(out, gltf, binary)
        print(f"{name}: halo turned about its own centre -> {out.relative_to(ROOT)}")
        return out
    gltf.setdefault("extensionsUsed", [])
    if "KHR_materials_unlit" not in gltf["extensionsUsed"]:
        gltf["extensionsUsed"].append("KHR_materials_unlit")
    image = {"name": "halo_basecolor", "mimeType": "image/png",
             "bufferView": add_view(gltf, binary, HALO_TEXTURE.read_bytes())}
    gltf.setdefault("images", []).append(image)
    gltf.setdefault("samplers", []).append({"magFilter": 9729, "minFilter": 9987, "wrapS": 33071, "wrapT": 33071})
    gltf.setdefault("textures", []).append({"sampler": len(gltf["samplers"]) - 1, "source": len(gltf["images"]) - 1})
    material = json.loads(json.dumps(halo_material))
    material["pbrMetallicRoughness"]["baseColorTexture"] = {"index": len(gltf["textures"]) - 1}
    # Each halo turns about its own centre: the MM8 lantern's halo sits on its axis (`true`, the whole mesh turns
    # about the model's axis), ours sit on off-centre lanterns (lamppost2's arm).
    material["extras"]["openyamm_billboard"] = "card"
    gltf["materials"].append(material)
    material_index = len(gltf["materials"]) - 1
    for mesh in gltf["meshes"]:
        fire = [gltf["accessors"][p["attributes"]["POSITION"]] for p in mesh["primitives"]
                if gltf["materials"][p["material"]].get("name") == "Fire"]
        if not fire:
            continue
        low = np.min([a["min"] for a in fire], 0)
        high = np.max([a["max"] for a in fire], 0)
        centre = (low + high) / 2
        # Kept inside the model's height: the engine scales a decoration by its binding height over the model's
        # height, so a halo past the base or top would resize the lamp (lantern2, lanternwall1 hang their flame low).
        everything = [gltf["accessors"][p["attributes"]["POSITION"]] for p in mesh["primitives"]]
        bottom = min(a["min"][1] for a in everything)
        top = max(a["max"][1] for a in everything)
        radius = min(RADIUS_PER_FLAME * (high[1] - low[1]), centre[1] - bottom, top - centre[1])
        # A square in the model's x/up plane (glTF x, y) facing +z, as the MM8 lantern's halo card.
        corners = np.array([[-1, -1, 0], [1, -1, 0], [1, 1, 0], [-1, 1, 0]], np.float32) * radius + centre
        attributes = {
            "POSITION": add_accessor(gltf, binary, corners.astype(np.float32), "VEC3", 5126, 34962, bounds=True),
            "NORMAL": add_accessor(gltf, binary, np.tile([0, 0, 1], (4, 1)).astype(np.float32), "VEC3", 5126, 34962),
            "TEXCOORD_0": add_accessor(gltf, binary, np.array([[0, 1], [1, 1], [1, 0], [0, 0]], np.float32),
                                       "VEC2", 5126, 34962),
            "COLOR_0": add_accessor(gltf, binary, np.tile(halo_colour, (4, 1)).astype(np.float32), "VEC4", 5126,
                                    34962),
        }
        indices = add_accessor(gltf, binary, np.array([0, 1, 2, 0, 2, 3], np.uint16), "SCALAR", 5123, 34963)
        mesh["primitives"].append({"attributes": attributes, "indices": indices, "material": material_index})
    out = HERE / "work" / source.name
    out.parent.mkdir(exist_ok=True)
    write_glb(out, gltf, binary)
    print(f"{name}: halo added -> {out.relative_to(ROOT)}")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--install", action="store_true")
    parser.add_argument("names", nargs="*", default=TARGETS)
    arguments = parser.parse_args()
    material, colour = mm8_halo()
    for name in arguments.names:
        out = add_halo(name, material, colour)
        if out is None or not arguments.install:
            continue
        check = subprocess.run([sys.executable, str(WINDING), str(out)], capture_output=True, text=True)
        print(check.stdout.strip().split("\n")[-1])
        result = subprocess.run([sys.executable, str(ROOT / "tools/install_model.py"), str(out), "--world", "mm9"],
                                cwd=ROOT, capture_output=True, text=True)
        print(f"{name}: install {'ok' if result.returncode == 0 else 'FAILED'}")
        if result.returncode != 0:
            print(result.stdout[-800:], result.stderr[-800:])
    return 0


if __name__ == "__main__":
    sys.exit(main())
