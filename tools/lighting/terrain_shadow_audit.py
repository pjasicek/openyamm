"""Independent terrain-only visibility audit for New Sorpigal's authored sun.

Run in Blender with: -- terrain_sun.npy report.json
This compares Cycles output against separate BVH rays, not runtime GPU performance.
"""
import json
import math
from pathlib import Path
import sys

import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_odm_file


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    if len(args) != 2:
        raise SystemExit('Expected terrain_sun.npy and output report.json')
    native = parse_odm_file(ROOT / 'assets_dev/worlds/mm6/maps/oute3.odm')['payload']
    heights = native['height_map']
    vertices = [((x - 64) * 512, (64 - y) * 512, heights[y * 128 + x] * 32)
                for y in range(128) for x in range(128)]
    triangles = []
    for y in range(127):
        for x in range(127):
            first = y * 128 + x
            triangles.extend([(first, first + 128, first + 1), (first + 1, first + 128, first + 129)])
    terrain = BVHTree.FromPolygons(vertices, triangles, all_triangles=True)
    profile = json.loads((ROOT / 'level_generation/lighting/baked_outdoors/profiles/mm6_oute3.yml').read_text())
    azimuth, elevation = math.radians(profile['azimuth']), math.radians(profile['elevation'])
    sun = Vector((math.cos(elevation) * math.cos(azimuth), math.cos(elevation) * math.sin(azimuth),
                  math.sin(elevation)))
    pixels = np.load(args[0])
    size = pixels.shape[0]
    shadowed, unoccluded = [], []
    for triangle in triangles:
        points = [Vector(vertices[index]) for index in triangle]
        normal = (points[1] - points[0]).cross(points[2] - points[0]).normalized()
        cosine = normal.dot(sun)
        # Exclude back-facing and near-tangent surfaces from this cast-shadow comparison.
        if cosine < .2:
            continue
        center = sum(points, Vector()) / 3
        origin = center + normal * .5
        hit = terrain.ray_cast(origin, sun, 150000)[0]
        u, v = (center.x + 32768) / 65024, (32768 - center.y) / 65024
        value = float(pixels[round(v * (size - 1)), round(u * (size - 1)), :3].mean())
        row = {'position': list(center), 'sun_cosine': cosine, 'baked_sun_mean': value,
               'ratio_to_unoccluded': value / (profile['sun_energy'] / math.pi * cosine)}
        if hit is None:
            unoccluded.append(row)
        else:
            row.update(blocker=list(hit), blocker_distance=(hit - origin).length)
            shadowed.append(row)
    shadowed.sort(key=lambda row: row['ratio_to_unoccluded'])
    shadow_ratio = float(np.median([row['ratio_to_unoccluded'] for row in shadowed]))
    lit_ratio = float(np.median([row['ratio_to_unoccluded'] for row in unoccluded]))
    report = {
        'sun_energy': profile['sun_energy'],
        'sun_direction': list(sun),
        'terrain_casts_on_terrain_samples': len(shadowed),
        'unoccluded_samples': len(unoccluded),
        'shadow_ratio_median': shadow_ratio,
        'lit_ratio_median': lit_ratio,
        'examples': shadowed[:10],
        'town_near_shadow_examples': [row for row in shadowed
                                     if -22000 < row['position'][0] < 1000
                                     and -21000 < row['position'][1] < 5000][:20],
        'passed': bool(shadowed) and shadow_ratio < .1 and .8 < lit_ratio < 1.2,
    }
    Path(args[1]).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if not isinstance(value, list)}, indent=2))
    if not report['passed']:
        raise RuntimeError('Terrain self-shadow audit failed; inspect report and bake')


if __name__ == '__main__':
    main()
