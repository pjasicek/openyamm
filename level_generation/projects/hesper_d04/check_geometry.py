"""Read back D4's compiled review fixes, including cell apertures and split furniture surfaces."""
import base64
import json
import struct
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parents[2] / 'util'))
from map_export import parse_blv_file

native = parse_blv_file(PROJECT / 'runtime/hes_d04.blv')['payload']
vertices = [tuple(v[k] for k in ('x', 'y', 'z')) for v in native['vertices']]
faces = [(f['texture_name'], [vertices[i] for i in f['vertex_indices']])
         for f in native['faces'] if not f['is_portal']]


def surfaces(point, axis):
    u, v = [i for i in range(3) if i != axis]
    found = []
    for material, polygon in faces:
        if not all(abs(p[axis] - point[axis]) < 0.5 for p in polygon):
            continue
        crosses = [(b[u] - a[u]) * (point[v] - a[v]) - (b[v] - a[v]) * (point[u] - a[u])
                   for a, b in zip(polygon, polygon[1:] + polygon[:1])]
        if all(c >= -0.5 for c in crosses) or all(c <= 0.5 for c in crosses):
            found.append(material)
    return set(found)


for y in (1614, 2178, 4118):
    assert not surfaces((4600, y, -320), 0), 'East cell front must stay open'
    assert surfaces((4800, y, -128), 2) == {'hkrib'}, 'Cell soffit must read as a framed recess'
    assert surfaces((4600, y, -100), 0) == {'hkrock'}, 'Wall above the opening must be closed'
for x in (-600, 300):
    for y in (2050, 2800, 3550):
        assert surfaces((x, y + 100, -352), 2) == {'hkfloor'}
        assert surfaces((x, y, -400), 1) == {'hkrib'}
        assert surfaces((x, y, -368), 1) == {'hktrim'}
assert surfaces((950, 2800, -480), 2) == {'hmslag'}
assert not surfaces((950, 2800, -384), 2), 'Trough basin must be open'
assert surfaces((860, 2800, -384), 2) == {'hmslag'}
for point, axis, key in (((7750, -1260, -1280), 2, 'hkfloor'), ((7750, -1140, -1280), 2, 'hkfloor'),
                         ((2300, 1320, -400), 1, 'hobone'), ((2300, 1400, -352), 2, 'hkfloor'),
                         ((4684, 300, -512), 2, 'hktrim'), ((7284, 300, -512), 2, 'hktrim')):
    assert surfaces(point, axis) == {key}, (point, key, surfaces(point, axis))
# The arrival stair's sloped roof starts at the Pens opening's soffit (z 128): no open gap above the opening.
stair_roof = [p for material, polygon in faces if material == 'hkceil'
              and all(2300 <= q[0] <= 3500 and 4500 <= q[1] <= 5600 for q in polygon)
              for p in polygon if abs(p[1] - 4500) < 0.5]
assert stair_roof and all(abs(p[2] - 128) < 0.5 for p in stair_roof), 'Stair roof must meet the Pens soffit'
assert surfaces((2700, 4468, 128), 2) == {'hkrib'} and surfaces((3100, 4468, 128), 2) == {'hkrib'}
semantic = json.loads((PROJECT / 'source/hes_d04.semantic.json').read_text())
sump = native['sectors'][semantic['sectors'].index('room_sump') + 1]
# MM8 ambient occupies 0x66; the parser's named field still uses the earlier sector layout.
assert struct.unpack_from('<h', base64.b64decode(sump['raw_record_base64']), 0x66)[0] == 18
assert any(e['name'].startswith('hes_d04_fire') and e['position'] == dict(x=2500, y=-300, z=-512)
           for e in native['entities'])
actors = json.loads((PROJECT / 'runtime/hes_d04.scene.yml').read_text())['initial_state']['actors']
assert [a['position'] for a in actors if a['group'] == 41] == [
    dict(x=4496, y=y, z=-512) for y in (1514, 1714, 2178, 4118)]
for event in (56, 57):
    assert any(f['face_param']['cog_triggered'] == event and f['texture_name'] == 'hkcage' for f in native['faces'])
print('PASS: stair roof meets the Pens soffit, open east cells, rib soffits, bunks, trough, drag marks, cache, platform trim, Sump ambient, bowl, Miners, cage events')
