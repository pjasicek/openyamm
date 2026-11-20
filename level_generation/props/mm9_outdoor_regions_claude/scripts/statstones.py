#!/usr/bin/env python3
"""The coloured stat stones: the Isle of Ashes' finished `statstone` (StatStone.ABC with the red skin, its marble
orb on a material of its own that scrolls and pulses: ../mm9_isleofashes_claude/scripts/build.py, orb_texture.py)
with another skin. Same ABC, same UVs: each variant swaps the base skin for its redrawn x4 skin
(../../mm9_skins_x4/work/x4/<skin>.png), the orb tile for one cut from that skin's marble block (the isle's
work/orb_region.json, mirrored side by side as orb_texture.py does) and tints the orb's glow by the marble's colour
(the isle's red emissive scaled). Images and materials are renamed to the variant (cooked textures are named by them).

    python3 level_generation/props/mm9_outdoor_regions_claude/scripts/statstones.py [--install]
"""
import io
import json
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
ISLE = REPO / "level_generation/props/mm9_isleofashes_claude"
SKINS = REPO / "level_generation/props/mm9_skins_x4"
BASE = REPO / "assets_source/worlds/mm9/models/mm9_deco_statstone.glb"
sys.path.insert(0, str(SKINS))
from skins import replace_images  # noqa: E402

# variant -> its skin's name in the skins inventory
VARIANTS = {"statstoneplain": "statstone_11a8b9", "statstonegreen": "statstonegreen",
            "statstonepurple": "statstonepurple", "statstoneyellow": "statstoneyellow"}
ISLE_EMISSIVE = np.array([0.30, 0.03, 0.02])      # the red orb's (the isle's finish.py ORB)


def png(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, "PNG", optimize=True)
    return buffer.getvalue()


def orb_tile(skin: Image.Image, region) -> tuple[Image.Image, np.ndarray]:
    u0, v0, u1, v1 = region
    w, h = skin.size
    box = (int(u0 * w) + 8, int((1 - v1) * h) + 8, int(u1 * w) - 8, int((1 - v0) * h) - 8)
    crop = skin.convert("RGB").crop(box).resize((256, 256))
    tile = Image.new("RGB", (512, 256))
    tile.paste(crop, (0, 0))
    tile.paste(crop.transpose(Image.FLIP_LEFT_RIGHT), (256, 0))
    return tile, np.array(crop, float).reshape(-1, 3).mean(0) / 255


def rename(path: Path, variant: str, emissive) -> None:
    """The JSON chunk only: images and materials statstone* -> <variant>*, the orb's emissive factor."""
    data = path.read_bytes()
    length = struct.unpack_from("<I", data, 12)[0]
    document = json.loads(data[20:20 + length])
    for item in document.get("images", []) + document.get("materials", []):
        if item.get("name", "").startswith("statstone"):
            item["name"] = variant + item["name"][len("statstone"):]
    orb = next(m for m in document["materials"] if m["name"] == f"{variant}_orb")
    orb["emissiveFactor"] = [round(float(v), 4) for v in emissive]
    body = json.dumps(document, separators=(",", ":")).encode()
    body += b" " * (-len(body) % 4)
    rest = data[20 + length:]
    out = data[:12] + struct.pack("<I", len(body)) + data[16:20] + body + rest
    path.write_bytes(out[:8] + struct.pack("<I", len(out)) + out[12:])


def main() -> int:
    region = json.loads((ISLE / "work/orb_region.json").read_text())
    _, red = orb_tile(Image.open(SKINS / "work/x4/statstone.png"), region)
    for variant, skin_name in VARIANTS.items():
        skin = Image.open(SKINS / f"work/x4/{skin_name}.png")
        tile, colour = orb_tile(skin, region)
        # the isle's emissive over its red marble's colour, applied to this marble's colour
        emissive = np.clip(colour * (ISLE_EMISSIVE.max() / max(red.max(), 1e-3)), 0, 1)
        emissive *= ISLE_EMISSIVE.max() / max(emissive.max(), 1e-3)
        out = HERE / f"work/mm9_deco_{variant}.glb"
        count = replace_images(BASE, {"statstone_basecolor": png(skin), "statstone_orb_basecolor": png(tile)}, out)
        if count != 2:
            sys.exit(f"{variant}: replaced {count} of 2 images in {BASE}")
        rename(out, variant, emissive)
        winding = subprocess.run([sys.executable, str(REPO / "level_generation/decorations/mm8_3d/animated/scripts/"
                                                      "check_winding.py"), str(out)], capture_output=True, text=True)
        print(variant, skin_name, "orb emissive", [round(float(v), 3) for v in emissive], winding.stdout.strip()[-80:])
        if "--install" in sys.argv:
            result = subprocess.run([sys.executable, str(REPO / "tools/install_model.py"), str(out), "--world", "mm9"],
                                    cwd=REPO, capture_output=True, text=True)
            print("  install", "ok" if result.returncode == 0 else "FAILED " + result.stderr[-300:])
    return 0


if __name__ == "__main__":
    sys.exit(main())
