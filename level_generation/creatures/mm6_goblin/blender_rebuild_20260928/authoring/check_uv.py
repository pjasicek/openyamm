"""Positive-area UV triangle overlap check against the actual GLB, excluding shared edges."""
from collections import defaultdict
import json
import math
import sys

from check_glb import Glb, ROOT


def cross(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def intersection_area(a, b):
    polygon = list(a)
    sign = 1 if cross(*b) > 0 else -1
    for p, q in zip(b, b[1:] + b[:1]):
        clipped = []
        for u, v in zip(polygon, polygon[1:] + polygon[:1]):
            du, dv = sign * cross(p, q, u), sign * cross(p, q, v)
            if du >= 0:
                clipped.append(u)
            if (du > 0 and dv < 0) or (du < 0 and dv > 0):
                t = du / (du - dv)
                clipped.append((u[0] + t * (v[0] - u[0]), u[1] + t * (v[1] - u[1])))
        polygon = clipped
        if len(polygon) < 3:
            return 0
    return abs(sum(u[0] * v[1] - u[1] * v[0] for u, v in zip(polygon, polygon[1:] + polygon[:1]))) / 2


def main():
    glb = Glb(ROOT / (sys.argv[1] if len(sys.argv) > 1 else 'delivery/mm6_goblin_rigged.glb'))
    triangles = []
    degenerate = []
    for mesh in glb.json['meshes']:
        for primitive in mesh['primitives']:
            uv = glb.accessor(primitive['attributes']['TEXCOORD_0'])
            ids = [v[0] for v in glb.accessor(primitive['indices'])]
            for offset in range(0, len(ids), 3):
                triangle = [uv[i] for i in ids[offset:offset + 3]]
                if abs(cross(*triangle)) < 1e-13:
                    degenerate.append([mesh['name'], offset // 3])
                triangles.append((mesh['name'], triangle))
    cells = defaultdict(list)
    overlaps = []
    checked = set()
    occupied = 0
    for index, (name, tri) in enumerate(triangles):
        occupied += abs(cross(*tri)) / 2
        x0, x1 = math.floor(min(p[0] for p in tri) * 128), math.floor(max(p[0] for p in tri) * 128)
        y0, y1 = math.floor(min(p[1] for p in tri) * 128), math.floor(max(p[1] for p in tri) * 128)
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for previous in cells[(x, y)]:
                    pair = previous, index
                    if pair in checked:
                        continue
                    checked.add(pair)
                    area = intersection_area(tri, triangles[previous][1])
                    if area > 1e-10:
                        overlaps.append({'a': triangles[previous][0], 'b': name, 'uv_area': area,
                                         'triangle_a': previous, 'triangle_b': index})
                cells[(x, y)].append(index)
    report = {'triangles': len(triangles), 'degenerate_uv_triangles': degenerate,
              'positive_area_overlap_pairs': len(overlaps), 'overlap_uv_area_sum': sum(p['uv_area'] for p in overlaps),
              'surface_uv_area_sum': occupied, 'overlaps': overlaps[:30], 'area_tolerance': 1e-10}
    (ROOT / 'delivery/uv_validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    assert not degenerate and not overlaps


if __name__ == '__main__':
    main()
