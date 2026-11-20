"""Read back D9's native faces at the integrator's reported gaps and check the retained set-piece dimensions."""
import base64
import json
import struct
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parents[2] / 'util'))
from map_export import parse_blv_file

native = parse_blv_file(PROJECT / 'runtime/hes_d09.blv')['payload']
vertices = [tuple(v[k] for k in ('x', 'y', 'z')) for v in native['vertices']]
faces = [(f['texture_name'], [vertices[i] for i in f['vertex_indices']])
         for f in native['faces'] if not f['is_portal']]


def surface(point, axis, texture):
    """A native polygon must cover this point in the requested plane, not merely share its bounding box."""
    u, v = [i for i in range(3) if i != axis]
    for material, polygon in faces:
        if material != texture or not all(abs(p[axis] - point[axis]) < 0.5 for p in polygon):
            continue
        crosses = [(b[u] - a[u]) * (point[v] - a[v]) - (b[v] - a[v]) * (point[u] - a[u])
                   for a, b in zip(polygon, polygon[1:] + polygon[:1])]
        if all(c >= -0.5 for c in crosses) or all(c <= 0.5 for c in crosses):
            return
    raise AssertionError(f'Missing {texture} surface at {point}, axis {axis}')


# Both halves of split ledges must retain the 64-unit floor and ceiling reveals (shots 04–06, 09).
for x, y in ((2632, 1300), (2632, 2900), (4968, 1300), (4968, 2900), (3100, 3368), (4500, 3368)):
    surface((x, y, 0), 2, 'hbfloor')
    surface((x, y, 768), 2, 'hbfold')
for point, axis in (((3328, 2100, -800), 0), ((4272, 2100, -800), 0),
                    ((3400, 1600, -800), 1), ((4200, 1600, -800), 1), ((3800, 2672, -800), 1)):
    surface(point, axis, 'hbfold')
# Doorway floors, soffits and jambs, including the chamber's two Birth Pit openings.
for x, y, z, jamb, axis in ((4700, 4432, 0, (4572, 4432, 200), 0),
                           (2900, 4432, 0, (2772, 4432, 200), 0),
                           (5632, 2800, -1536, (5632, 2672, -1336), 1),
                           (6032, 2964, -2944, (6032, 2740, -2744), 1),
                           (3500, 3032, -2944, (3244, 3032, -2744), 0),
                           (5200, 3032, -2944, (4944, 3032, -2744), 0)):
    surface((x, y, z), 2, 'hbfloor')
    surface((x, y, z + 400), 2, 'hbfold')
    surface(jamb, axis, 'hbfold')
# The Royal ceiling is now one continuous slope, 424+ above the 16-unit treads.
royal_roof = [points for material, points in faces if material == 'hbceil' and
              all(abs(p[2] - (-2496 + (p[1] - 4) * 1408 / 2332)) < 1 for p in points)]
assert royal_roof and min(p[1] for face in royal_roof for p in face) == 4
assert max(p[1] for face in royal_roof for p in face) == 2336
for x, y, z in ((3450, 1700, -1568), (4700, 2650, -1568), (3150, 100, -2976), (5500, 100, -2976)):
    surface((x, y, z), 2, 'hbacid')

for x, y in ((3914, 4564), (4914, 4564), (3914, 5164), (4914, 5164)):
    surface((x + 200, y + 200, 200), 2, 'hbfloor')
    surface((x, y + 200, 100), 0, 'hbvatrim')
for x in (3300, 4300, 5300):
    surface((x + 100, 3700, -3200), 2, 'hbfold')
    surface((x + 100, 3400, -3072), 1, 'hbfold')
for point, axis in (((6900, 3264, -2960), 0), ((7500, 3264, -2960), 0),
                    ((7200, 2964, -2960), 1), ((7200, 3564, -2960), 1)):
    surface(point, axis, 'hbvatrim')

glb = (PROJECT / 'source/hes_d09.glb').read_bytes()
gltf = json.loads(glb[20:20 + struct.unpack_from('<I', glb, 12)[0]])
rooms = [gltf['nodes'][i]['name'].lower() for i in gltf['scenes'][gltf['scene']]['nodes']
         if gltf['nodes'][i]['name'].startswith('ROOM_')]
assert native['version'] == 8 and len(rooms) == len(native['sectors']) - 1 == 42
for name, sector in zip(rooms, native['sectors'][1:]):
    expected = 12
    if name.startswith(('room_east_ledge', 'room_north_ledge', 'room_west_ledge', 'room_rim',
                        'room_well', 'room_low_', 'room_descent', 'room_passage', 'room_shaft')) or name == 'room_royal':
        expected = 14
    elif name.startswith('room_mother'):
        expected = 10
    elif name.startswith('room_pits'):
        expected = 18
    # MM8 sector ambient is at 0x66; map_export's named field uses the older 0x62 layout.
    ambient = struct.unpack_from('<h', base64.b64decode(sector['raw_record_base64']), 0x66)[0]
    assert ambient == expected, (name, ambient, expected)
assert len(native['lights']) == 57
print('PASS: native reveal/slab closure, sloped Royal ceiling and shallow acid edges, 200-unit cribs, three 256-deep pits, lift sides, ambient')
