#!/usr/bin/env python3
"""Where the hanging cages sit in 7d27: each 7dec05/06/07 entity's position and the nearest face below (floor) and
above (ceiling) its x, y (vertical ray against every BLV face polygon, invisible faces included and flagged).
Usage: cage_placements.py [map.blv] [names...]"""
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO / 'tools'))
import export_indoor_scene_yml as blv  # noqa: E402

path = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / 'assets_dev/worlds/mm7/maps/7d27.blv'
names = set(sys.argv[2:]) or {'7dec05', '7dec06', '7dec07'}
data = blv.parse_indoor_blv(path)
verts = np.array([(v['x'], v['y'], v['z']) for v in data['vertices']], float)
faces = data['face_vertex_ids']
attrs = data['face_attributes']

reader = blv.ByteReader(path, path.read_bytes())
layout = blv.detect_blv_layout(reader)
face_data = reader.read_i32(blv.FACE_DATA_SIZE_OFFSET, 'face data')
sector_data = reader.read_i32(blv.SECTOR_R_DATA_SIZE_OFFSET, 'sector data')
sector_lights = reader.read_i32(blv.SECTOR_RL_DATA_SIZE_OFFSET, 'sector lights')
offset = blv.SECTION_OFFSET
offset += 4 + reader.read_i32(offset, 'vertices') * blv.VERTEX_RECORD_SIZE
count = reader.read_i32(offset, 'faces')
offset += 4 + count * layout['face_record_size'] + face_data + count * blv.TEXTURE_NAME_SIZE
offset += 4 + reader.read_i32(offset, 'params') * (blv.FACE_PARAM_RECORD_SIZE + blv.FACE_PARAM_NAME_SIZE)
offset += 4 + reader.read_i32(offset, 'sectors') * layout['sector_record_size'] + sector_data + sector_lights
offset += 4
entities = reader.read_i32(offset, 'entities')
records = offset + 4
names_at = records + entities * layout['sprite_record_size']


def hits(x, y):
    """z of every face crossing the vertical line through x, y."""
    out = []
    for index, ids in enumerate(faces):
        if len(ids) < 3:
            continue
        p = verts[ids]
        if not (p[:, 0].min() <= x <= p[:, 0].max() and p[:, 1].min() <= y <= p[:, 1].max()):
            continue
        normal = np.cross(p[1] - p[0], p[2] - p[0])
        for k in range(2, len(p)):
            n = np.cross(p[k - 1] - p[0], p[k] - p[0])
            if abs(n[2]) > abs(normal[2]):
                normal = n
        if abs(normal[2]) < 1e-6:
            continue
        inside = False
        j = len(p) - 1
        for i in range(len(p)):
            if (p[i, 1] > y) != (p[j, 1] > y):
                xc = p[j, 0] + (y - p[j, 1]) * (p[i, 0] - p[j, 0]) / (p[i, 1] - p[j, 1])
                if x < xc:
                    inside = not inside
            j = i
        if inside:
            z = p[0, 2] - (normal[0] * (x - p[0, 0]) + normal[1] * (y - p[0, 1])) / normal[2]
            out.append((z, index, bool(attrs[index] & blv.FACE_ATTRIBUTE_INVISIBLE)))
    return sorted(out)


for index in range(entities):
    name = reader.read_fixed_string(names_at + index * blv.SPRITE_NAME_SIZE, blv.SPRITE_NAME_SIZE, 'name').lower()
    if name not in names:
        continue
    r = records + index * layout['sprite_record_size']
    x, y, z = (reader.read_i32(r + 4 + 4 * k, 'pos') for k in range(3))
    zs = hits(x, y)
    below = [h for h in zs if h[0] <= z + 1]
    above = [h for h in zs if h[0] > z + 1]
    floor = below[-1][0] if below else None
    ceiling = above[0][0] if above else None
    print(f'{name} #{index} at ({x}, {y}, {z}) floor {floor} ceiling {ceiling} '
          f'(z - floor {None if floor is None else round(z - floor)}, ceiling - z '
          f'{None if ceiling is None else round(ceiling - z)}) faces {[(round(h[0]), h[2]) for h in zs]}')
