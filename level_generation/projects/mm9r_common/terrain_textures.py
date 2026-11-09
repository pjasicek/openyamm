#!/usr/bin/env python3
"""
The ground textures of an MM9 region (its `Terrain` class models), for choosing overrides.yml `terrain.materials`
(terrain_blend.py; devdocs/mm9_rework/OUTDOOR_BLV_ALL.md): each texture's file stem, area share, how much of it faces
up, and a contact sheet of the textures (MM9's own bitmaps from the old import) to look at before mapping them.

    python3 level_generation/projects/mm9r_common/terrain_textures.py THJORGARD [--sheet out.png]
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dungeon.source import poly_ring, read_dat_world  # noqa: E402


def polygon_area_normal(points: np.ndarray) -> tuple[float, float]:
    """Area and the normal's up component (LT: Y is up) of a planar polygon."""
    normal = np.zeros(3)
    for k in range(len(points)):
        normal += np.cross(points[k], points[(k + 1) % len(points)])
    length = float(np.linalg.norm(normal))
    return length / 2.0, (abs(normal[1]) / length if length else 0.0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("map")
    parser.add_argument("--sheet")
    args = parser.parse_args()
    name = args.map.upper()
    world = read_dat_world(ROOT / f"mm9/extracted/WORLDS/WORLDS/{name}.dat")
    classes = {}
    for o in world.objects:
        properties = {p.name: p.value for p in o.properties}
        classes[str(properties.get("Name", ""))] = o.name
    area, up = defaultdict(float), defaultdict(float)
    for model in world.world_models:
        if classes.get(model.name) != "Terrain" and not model.name.lower().startswith(("terrain", "earthquake")):
            continue
        for poly in model.polies:
            ring = poly_ring(poly)
            if len(ring) < 3:
                continue
            a, u = polygon_area_normal(np.array([model.points[i] for i in ring], float))
            texture = model.textures[model.surfaces[poly.surface_index].texture_index]
            stem = Path(str(texture).replace("\\", "/")).stem.lower()
            area[stem] += a
            up[stem] += a * u
    total = sum(area.values()) or 1.0
    aliases = yaml.safe_load((ROOT / f"assets_editor_dev/worlds/mm9/maps/{name.lower()}.material_aliases.yml").read_text())
    bitmaps = {Path(str(e["source_texture"]).replace("\\", "/")).stem.lower(): e.get("emitted_bitmap", "")
               for e in aliases["textures"]}
    rows = sorted(area.items(), key=lambda kv: -kv[1])
    for stem, a in rows:
        print(f"  {stem:28} {100 * a / total:5.1f} %  up {up[stem] / a:4.2f}  {bitmaps.get(stem, '?')}")
    if args.sheet:
        tile, columns = 256, 4
        shown = [(s, a) for s, a in rows if bitmaps.get(s) and 100 * a / total >= 0.5]
        sheet = Image.new("RGB", (columns * tile, ((len(shown) + columns - 1) // columns) * (tile + 20)), "white")
        draw = ImageDraw.Draw(sheet)
        for k, (stem, a) in enumerate(shown):
            path = (ROOT / "assets_editor_dev/worlds/mm9/maps" / bitmaps[stem]).resolve()
            x, y = (k % columns) * tile, (k // columns) * (tile + 20)
            try:
                sheet.paste(Image.open(path).convert("RGB").resize((tile, tile)), (x, y + 20))
            except OSError:
                pass
            draw.text((x + 4, y + 4), f"{stem} {100 * a / total:.0f}%", fill="black")
        sheet.save(args.sheet)
    return 0


if __name__ == "__main__":
    sys.exit(main())
