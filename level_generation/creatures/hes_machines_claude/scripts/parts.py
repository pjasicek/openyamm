"""Split a Meshy return into rigid parts (face attribute `part`) and clean it.

Parts: 0 mount (the turret's static pedestal up to and with the gold ring: its own decoration), 1 root (the turret's
turntable; the whole cell or conduit), 2 head (the turret's fork yoke and hub trunnions: yaw), 3 barrel (the gun
housing, lens pods and barrel: pitch), 4 recoil (the barrel's front sleeves and muzzle: slides back). Every connected
component goes whole to one part, by its centroid (rules below, on the oriented mesh). Components of fewer than 4
vertices are deleted; then merge by distance (0.1 mm) and consistent outward normals per part.
Writes work/<name>_parts_raw.blend (object <name>, face attribute `part`, custom properties pivot / ring_top).
Args: -- <name>"""
import json
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'scripts'))
import machines_common as mc  # noqa: E402

NAME = sys.argv[sys.argv.index('--') + 1]
TURRET = NAME == 'starport_turret'
RING_TOP = 0.599 if TURRET else 0.0              # top of the turret's gold turning ring (component 53)
PIVOT = (0.0, 0.10, 0.97) if TURRET else (0.0, 0.0, 0.0)   # between the trunnion hubs (Meshy put them 0.3 m apart in y)
MOUNT_TURN = 45.0   # the return's pedestal is diagonal to the barrel: turn it so one face looks to the front (-y)

obj = mc.orient(mc.import_glb(mc.RAW[NAME]), NAME)
bm = bmesh.new(); bm.from_mesh(obj.data)
labels = mc.component_labels(bm)
co = np.array([v.co[:] for v in bm.verts])
stats = [(int((labels == c).sum()), co[labels == c].mean(0)) for c in range(labels.max() + 1)]


def part_of(c):
    n, mid = stats[c]
    if n < 4:
        return -1
    if not TURRET:
        return 1
    x, y, z = mid
    if z < 0.585:
        return 0
    if z < 0.72 and np.hypot(x, y) < 0.3:
        return 1
    if z < 0.9 or (abs(x) > 0.36 and 0.85 < z < 1.1):
        return 2
    if y < -0.8 and z > 1.05 and abs(x) < 0.2:
        return 4
    return 3


comp_part = [part_of(c) for c in range(len(stats))]
fpart = bm.faces.layers.int.new('part')
for f in bm.faces:
    f[fpart] = comp_part[labels[f.verts[0].index]]
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[fpart] < 0], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
if TURRET:
    rot = Matrix.Rotation(np.radians(MOUNT_TURN), 4, 'Z')
    for v in {v for f in bm.faces if f[fpart] == 0 for v in f.verts}:
        v.co = rot @ v.co
for p in range(5):
    faces = [f for f in bm.faces if f[fpart] == p]
    if not faces:
        continue
    bmesh.ops.remove_doubles(bm, verts=list({v for f in faces for v in f.verts}), dist=0.0001)
    faces = [f for f in bm.faces if f[fpart] == p]
    bmesh.ops.recalc_face_normals(bm, faces=faces)
bm.to_mesh(obj.data); bm.free()
counts = {}
for poly, value in zip(obj.data.polygons, obj.data.attributes['part'].data):
    counts[value.value] = counts.get(value.value, 0) + len(poly.vertices) - 2
print('PART_TRIS', json.dumps(dict(sorted(counts.items()))), 'components',
      {p: comp_part.count(p) for p in range(-1, 5)})
obj['pivot'] = PIVOT
obj['ring_top'] = RING_TOP
os.makedirs(os.path.join(HERE, 'work'), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', f'{NAME}_parts_raw.blend'))
print('SAVED')
