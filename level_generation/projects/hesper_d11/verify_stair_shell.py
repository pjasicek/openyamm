"""Check the compiled surfaces behind the desktop review's three D11 defects."""
import json
from pathlib import Path
import sys

import numpy as np

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parents[2] / 'util'))
from map_export import parse_blv_file

path = Path(sys.argv[1]) if len(sys.argv) > 1 else PROJECT / 'runtime/hes_d11.blv'
data = parse_blv_file(path)['payload']
vertices = np.array([[v['x'], v['y'], v['z']] for v in data['vertices']], float)
names = sorted(json.loads((PROJECT / 'source/hes_d11.semantic.json').read_text())['sectors'])
faces = [(f, vertices[f['vertex_indices']]) for f in data['faces'] if not f['is_portal']]
portals = [(f, vertices[f['vertex_indices']]) for f in data['faces'] if f['is_portal']]


def surface(point, room, texture):
    """Point containment in the compiler's triangles, including their boundaries."""
    for record, points in faces:
        if not names[record['room_number'] - 1].startswith('room_' + room):
            continue
        if record['texture_name'] != texture:
            continue
        for i in range(1, len(points) - 1):
            a, b, c = points[0], points[i], points[i + 1]
            u, v, w = b - a, c - a, np.asarray(point) - a
            normal = np.cross(u, v)
            if np.linalg.norm(normal) < .01 or abs(np.dot(w, normal)) > np.linalg.norm(normal):
                continue
            gram = np.array([[u @ u, u @ v], [u @ v, v @ v]])
            s, t = np.linalg.solve(gram, [w @ u, w @ v])
            if s >= -1e-6 and t >= -1e-6 and s + t <= 1 + 1e-6:
                return True
    return False


# The lowered soffit's exposed side used to open onto the void above it.
for y in (1900, 2200, 2500, 2750):
    slope = 448 + (y - 1800) * 1280 / 2000
    assert surface((3000, y, (slope + 1088) / 2), 'breach', 'hsrib'), ('soffit side', y)

# The raised breach sector must own the hull wall and the hipped roof within its shaft.
for y in (3100, 3400, 3700):
    for z, texture in ((1320, 'hsrib'), (1700, 'hsrib'), (2200, 'hsmemb')):
        assert surface((3600, y, z), 'breach', texture), ('shaft hull', y, z)
assert any(f['texture_name'] == 'hsceil' and names[f['room_number'] - 1].startswith('room_breach')
           and p[:, 2].min() >= 2272 and p[:, 2].max() > p[:, 2].min() for f, p in faces), 'hipped shaft roof'

# Large stair skirts use wall material; bone trim is confined to risers and the shallow rail.
for x in (800, 1200):
    for y in (8100, 8500, 9000):
        assert surface((x, y, 1400), 'quarters', 'hpwall'), ('gilded stair side', x, y)
        assert not surface((x, y, 1400), 'quarters', 'hptrim'), ('oversized trim', x, y)

# Every landing portal faces its front sector: the stair sector inside the shaft, the upper room outside it.
# The renderer culls a portal seen from behind, which left the Cradles black from the breach stair's top.
SHAFTS = [('rib_port', 'quarters', (120, 520, 8500, 9500)), ('rib_star', 'dormitory', (3080, 3480, 8500, 9500)),
          ('quarters', 'core', (800, 1200, 7800, 8560)), ('vault', 'duel', (1900, 2900, 1250, 1650)),
          ('breach', 'cradles', (3000, 3600, 3000, 3800))]
for lower, upper, (x0, x1, y0, y1) in SHAFTS:
    centre = np.array([(x0 + x1) / 2, (y0 + y1) / 2])
    count = 0
    for record, points in portals:
        rooms = [names[record[k] - 1] for k in ('room_number', 'room_behind_number')]
        if not (any(r.startswith('room_' + lower) for r in rooms) and any(r.startswith('room_' + upper) for r in rooms)):
            continue
        normal = np.cross(points[1] - points[0], points[2] - points[0])
        if abs(normal[2]) > .5 * np.linalg.norm(normal):
            continue
        inward = normal[:2] @ (centre - points[0, :2]) > 0
        assert inward == rooms[0].startswith('room_' + lower), ('landing portal faces away', lower, rooms, points)
        count += 1
    assert count >= 2, ('landing portals', lower, count)

# The Starboard Gallery's door at the breach stair's head opens into the stair sector that owns the landing.
door = [names[f['room_number'] - 1] + '|' + names[f['room_behind_number'] - 1] for f, p in portals
        if abs(p[:, 1] - 3800).max() < .5 and p[:, 0].min() >= 3152 and p[:, 0].max() <= 3408]
assert door and all('room_breach_1' in d and 'room_gal_star' in d for d in door), door

# Every chamfered corner keeps its diagonal wall (float32 clipping used to drop some, leaving black slots).
semantic = json.loads((PROJECT / 'source/hes_d11.semantic.json').read_text())
for room, outline in semantic['room_footprints'].items():
    for (ax, ay), (bx, by) in zip(outline, outline[1:] + outline[:1]):
        if ax == bx or ay == by:
            continue
        middle = ((ax + bx) / 2, (ay + by) / 2)
        assert any(names[f['room_number'] - 1].startswith('room_' + room) and abs(p[:, 2].max() - p[:, 2].min()) > 1
                   and abs(p[:, 0].mean() - middle[0]) < 80 and abs(p[:, 1].mean() - middle[1]) < 80
                   and abs(np.cross(p[1] - p[0], p[2] - p[0])[2]) < 1 for f, p in faces), ('chamfer wall', room, middle)

print('PASS: breach soffit sides, shaft hull/hipped roof, landing portal facing, chamfer walls and Noble Hall stair '
      'materials')
