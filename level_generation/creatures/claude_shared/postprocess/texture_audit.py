#!/usr/bin/env python3
"""Texture state of a world's 3D models as the cook treats them (tools/cook/model_textures.yml, the creature class).

Per model: base colour size, normal map size and relief (90th percentile tilt |xy| over relief texels, as
tools/cook_models.py normal_relief measures it), the authored normalTexture.scale and the multiplier the cook applies
(normal_strength), and the material's openyamm_specular. Use it to spot maps the cook cannot rescue: no normal map, a
relief so weak that even the 3x lift stays flat, a relief already strong (left as authored), or specular off.

    texture_audit.py [--world mm8] [--match <file glob>]
"""
import argparse
import fnmatch
import io
from pathlib import Path
import sys

import yaml
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "tools"))
import cook_models  # noqa: E402

ROOT = cook_models.ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--world", default="mm8")
    parser.add_argument("--match", default="*.glb")
    args = parser.parse_args()
    rules = cook_models.Rules(ROOT / "tools/cook/model_textures.yml")
    weak = 0
    for path in sorted((ROOT / "assets_source/worlds" / args.world / "models").glob("*.glb")):
        if not fnmatch.fnmatch(path.name, args.match):
            continue
        relative = path.relative_to(ROOT / "assets_source").as_posix()
        document, binary = cook_models.read_glb(path.read_bytes())
        sidecar_path = path.with_suffix(".cook.yml")
        sidecar = yaml.safe_load(sidecar_path.read_text()) if sidecar_path.exists() else {}
        lines = []
        for material in document.get("materials", []):
            colour = material.get("pbrMetallicRoughness", {}).get("baseColorTexture")
            if colour is None:
                continue
            png = cook_models.image_bytes(document, binary, document["textures"][colour["index"]]["source"])
            size = "x".join(map(str, Image.open(io.BytesIO(png)).size))
            specular = material.get("extras", {}).get("openyamm_specular", 1)
            normal = material.get("normalTexture")
            if normal is None:
                lines.append(f"{material.get('name', '?')[:24]}: colour {size}, no normal map, specular {specular}")
                continue
            normal_png = cook_models.image_bytes(document, binary, document["textures"][normal["index"]]["source"])
            relief = cook_models.normal_relief(normal_png)
            strength = cook_models.normal_strength(rules, relative, sidecar, normal_png)
            effective = relief * strength * normal.get("scale", 1.0)
            weak += 0 < effective < 0.15
            nsize = "x".join(map(str, Image.open(io.BytesIO(normal_png)).size))
            lines.append(f"{material.get('name', '?')[:24]}: colour {size}, normal {nsize} relief {relief:.3f}"
                         f" x{normal.get('scale', 1.0):.2f} authored x{strength:.2f} cook = {effective:.2f}"
                         f"{' flat map' if relief == 0 else ' WEAK' if effective < 0.15 else ''}, specular {specular}")
        unique = list(dict.fromkeys(lines))
        print(f"{path.name}: " + (" | ".join(unique[:3]) + (f" | +{len(unique) - 3} more" if len(unique) > 3 else "")
                                  if unique else "no textured materials"))
    print(f"\n{weak} materials whose relief stays below 0.15 after the cook's lift (flat maps not counted)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
