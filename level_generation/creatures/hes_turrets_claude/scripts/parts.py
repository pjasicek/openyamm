"""Split a Meshy return into the turret's rigid parts and clean it: v2 step 1.

Every connected component of the Smart Topology return goes whole to one part (component indices are those of
turret_common.component_labels on the fixed raw file; scripts/components.py renders them labelled):
  0 mount  - static pedestal up to and with the gold turning ring (the hes_*_mount decoration)
  1 root   - the turntable on the ring (B_Root: turns with the actor's facing, not animated)
  2 head   - Ward: the yoke arm and its elbow hubs; Bastion: column, cables, dome, shoulders, lenses (B_Head)
  3 barrel - Ward: the gun housing, lens pods, pennant and barrel shroud; Bastion: the twin barrels (B_Barrel)
  4 recoil - Ward only: the barrel cluster, collars and muzzle, sliding back in the shroud (B_Recoil)
  5 cable  - Ward only: the two cable loops from the yoke into the housing (blended B_Head -> B_Barrel by height)
Components of fewer than 4 vertices (stray triangles) are deleted. The Ward's mount is turned -45 degrees about the
yaw axis so its hatch faces the front (-y) like the barrel (the return has the pedestal square to the camera of the
three-quarter master). Then: merge by distance (0.1 mm), consistent outward normals, smooth shading with sharp
edges over SHARP_DEG, and a limited collapse decimation of the dense parts to the LOD0 budget.
Writes work/<name>_parts.blend (objects <name> with face attribute `part`, and the pivots as custom properties).
Args: -- <ward_turret|gate_bastion>"""
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'scripts'))
import turret_common as tc  # noqa: E402

NAME = sys.argv[sys.argv.index('--') + 1]
SHARP_DEG = 38.0
WARD = NAME == 'ward_turret'

if WARD:
    RING_TOP = 0.599                               # top of the gold ring (component 63)
    ROOT = {11}
    HEAD = {3, 53, 34, 28, 33, 46, 49, 115, 104}
    CABLE = {86, 1}
    RECOIL = {36, 101, 42, 13, 55, 69, 75, 47, 52, 29, 64, 6, 23, 51, 56, 73}
    PIVOT = (0.0, 0.16, 0.92)                      # the elbow hubs' axis (components 33, 46)
    MOUNT_TURN = -45.0
else:
    RING_TOP = 1.023                               # top of the gold turning ring (component 21)
    ROOT = set()
    HEAD = set()
    CABLE = set()
    RECOIL = set()
    PIVOT = (-0.72, -0.25, 1.76)                   # between the two barrels where they enter the dome
    MOUNT_TURN = 0.0
    BARREL_CUT_Y = -0.05                           # the barrels end here inside the dome (their rear would poke
                                                   # out of its top when they pitch down)

obj = tc.import_raw(NAME)
bm = bmesh.new(); bm.from_mesh(obj.data)
labels = tc.component_labels(bm)
co = np.array([v.co[:] for v in bm.verts])
ncomp = labels.max() + 1
stats = []
for c in range(ncomp):
    p = co[labels == c]
    stats.append((len(p), p.min(0), p.max(0), p.mean(0)))


def part_of(c):
    n, lo, hi, mid = stats[c]
    if n < 4:
        return -1
    if WARD:
        if c in ROOT:
            return 1
        if mid[2] < RING_TOP:
            return 0
        if c in HEAD:
            return 2
        if c in CABLE:
            return 5
        if c in RECOIL:
            return 4
        return 3
    if mid[2] < RING_TOP - 0.005 or hi[2] <= RING_TOP + 0.002:
        return 0
    if mid[0] < -0.17 and mid[1] < 0.1 and mid[2] > 1.38:
        return 3
    return 2


comp_part = [part_of(c) for c in range(ncomp)]
fpart = bm.faces.layers.int.new('part')
for f in bm.faces:
    f[fpart] = comp_part[labels[f.verts[0].index]]
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[fpart] < 0], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
if MOUNT_TURN:
    rot = Matrix.Rotation(math.radians(MOUNT_TURN), 4, 'Z')
    for v in {v for f in bm.faces if f[fpart] == 0 for v in f.verts}:
        v.co = rot @ v.co
if not WARD:
    faces = [f for f in bm.faces if f[fpart] == 3]
    geom = list({v for f in faces for v in f.verts}) + list({e for f in faces for e in f.edges}) + faces
    bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=(0, BARREL_CUT_Y, 0), plane_no=(0, 1, 0))
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[fpart] == 3 and f.calc_center_median().y > BARREL_CUT_Y],
                     context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
for p in range(6):
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
print('PART_TRIS', json.dumps(dict(sorted(counts.items()))), 'components', {p: comp_part.count(p) for p in range(-1, 6)})
obj['pivot'] = PIVOT
obj['ring_top'] = RING_TOP
os.makedirs(os.path.join(HERE, 'work'), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', f'{NAME}_parts_raw.blend'))
print('SAVED')
