#!/usr/bin/env python3
"""
Vertical sections of the DAT world for planning (LT units): work/section_<name>.png, solid voxels dark, air light,
nonsolid and invisible faces marked.

    python3 level_generation/projects/mm9r_bathhouse/section.py <name> x|z <coordinate> <low> <high> [ylow yhigh]
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon.source import Project, Source, classify_models  # noqa: E402


def main() -> int:
    name, axis, coord, low, high = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
    ylow, yhigh = (float(sys.argv[6]), float(sys.argv[7])) if len(sys.argv) > 7 else (-1540.0, 680.0)
    project = Project.load(PROJECT, install=False)
    source = Source(project)
    plan = classify_models(source)
    polygons = [p for m in plan["static"] + sorted(plan["movers"]) for p in source.polygons(m)]
    a, b = (0, 2) if axis == "x" else (2, 0)     # a: the cut axis, b: the horizontal axis of the image
    scale = 1.0
    width, height = int((high - low) * scale) + 1, int((yhigh - ylow) * scale) + 1
    image = Image.new("RGB", (width, height), (235, 235, 225))
    draw = ImageDraw.Draw(image)
    to = lambda u, y: ((u - low) * scale, (yhigh - y) * scale)      # noqa: E731
    colours = {"static": (20, 20, 30), "invisible": (220, 40, 200), "nonsolid": (30, 150, 230)}
    for polygon in polygons:
        ring = polygon.points
        crossings = []
        for i in range(len(ring)):
            p, q = ring[i], ring[(i + 1) % len(ring)]
            dp, dq = p[a] - coord, q[a] - coord
            if dp == dq:
                continue
            if (dp <= 0 < dq) or (dq <= 0 < dp):
                t = dp / (dp - dq)
                crossings.append(p + (q - p) * t)
        if len(crossings) == 2:
            draw.line([to(crossings[0][b], crossings[0][1]), to(crossings[1][b], crossings[1][1])],
                      fill=colours[polygon.role], width=2)
    for o in source.objects:
        if o["class"] in ("BlueWater", "DamageBrush") and o["name"] in source.models:
            pts = np.array(source.models[o["name"]].points, float)
            lo, hi = pts.min(0), pts.max(0)
            if lo[a] <= coord <= hi[a]:
                draw.rectangle([to(lo[b], hi[1]), to(hi[b], lo[1])], outline=(0, 90, 255) if o["class"] == "BlueWater"
                               else (255, 0, 0), width=2)
                draw.text(to(lo[b] + 4, hi[1] - 4), o["name"], fill=(0, 60, 200))
    for o in source.objects:
        pos = o["properties"].get("Pos")
        if pos and abs(pos[a] - coord) < 160 and low <= pos[b] <= high and o["class"] not in ("Light", "DirLight", "AmbientSound"):
            x, y = to(pos[b], pos[1])
            draw.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(230, 120, 0))
            draw.text((x + 5, y - 5), o["name"], fill=(160, 70, 0))
    for gy in range(int(ylow // 128 * 128), int(yhigh) + 128, 128):
        draw.line([to(low, gy), to(high, gy)], fill=(190, 190, 200))
        draw.text(to(low + 2, gy), str(gy), fill=(120, 60, 60))
    for gu in range(int(low // 256 * 256), int(high) + 256, 256):
        draw.line([to(gu, ylow), to(gu, yhigh)], fill=(190, 190, 200))
        draw.text(to(gu + 2, yhigh - 12), str(gu), fill=(120, 60, 60))
    image.save(PROJECT / f"work/section_{name}.png")
    print(PROJECT / f"work/section_{name}.png", image.size)
    return 0


if __name__ == "__main__":
    sys.exit(main())
