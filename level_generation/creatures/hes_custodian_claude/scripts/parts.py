"""Split the Smart Topology return (meshy/custodian_st_v1) into the Custodian's rigid parts and clean it.

Every connected component goes whole to one part (component indices of cust_common.component_labels on the fixed raw
file; scripts/components.py and arm_labels.py render them, review/arm_labels.png), except the two long cables of each
arm, which run from the shoulder round to the disc housing and are blended along the arm (vertex group weights from
their position along the shoulder -> elbow -> hub polyline).

Parts (= bones, see rig.py): 1 Body (sphere shells, rings, belt, eye, vents, inner cables, arm mounts, sensor post),
2 Sensor (the sensor head), 3/6 Shoulder_L/R (shoulder hub, upper-arm rods and pistons), 4/7 Elbow_L/R (elbow hubs,
forearm, disc housing and its small parts), 5/8 Disc_L/R (saw disc and its hub: they spin). Left = +x.

Raw -> metres: the sphere's centre (0, 0.08, 0.05) to the origin's axis, scaled so the sphere is 2.4 m across
(raw 0.66 -> x3.636), then lifted so the lowest point (the disc rims) is at z = 0. Components under 12 vertices are
dropped; merge by distance 0.1 mm and consistent normals per part.
Writes work/parts.blend (object Custodian, face attribute `part`, vertex groups for the cables, joint positions as
custom properties `joints`). Args: none."""
import json
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cust_common as cc  # noqa: E402

LEFT = {'mount': [38], 'shoulder': [17, 57, 33, 15, 39], 'elbow': [1, 36, 63, 65, 18, 5, 45, 9],
        'disc': [24, 19], 'cable': [28, 50]}
RIGHT = {'mount': [54], 'shoulder': [31, 14, 25, 6, 35], 'elbow': [27, 44, 47, 66, 41, 16, 59, 42],
         'disc': [7, 23], 'cable': [0, 21]}
SENSOR_HEAD = [49]
PART = {'Body': 1, 'Sensor': 2, 'Shoulder_L': 3, 'Elbow_L': 4, 'Disc_L': 5, 'Shoulder_R': 6, 'Elbow_R': 7, 'Disc_R': 8}
CENTRE = Vector((0.0, 0.08, 0.05))
SCALE = 2.4 / 0.66
# raw joint centres (left arm; the right arm mirrors x): shoulder hub, elbow hub axis, disc hub
RAW_JOINTS = {'Shoulder_L': (0.385, 0.046, 0.020), 'Elbow_L': (0.44, 0.035, -0.14), 'Disc_L': (0.434, -0.227, -0.305),
              'Shoulder_R': (-0.385, 0.046, 0.020), 'Elbow_R': (-0.44, 0.035, -0.14), 'Disc_R': (-0.434, -0.226, -0.30)}

obj = cc.import_raw()
bm = bmesh.new(); bm.from_mesh(obj.data)
labels = cc.component_labels(bm)
ncomp = labels.max() + 1
sizes = np.bincount(labels, minlength=ncomp)
comp_part = np.ones(ncomp, int)                       # default Body
for side, spec in (('L', LEFT), ('R', RIGHT)):
    for c in spec['shoulder']:
        comp_part[c] = PART['Shoulder_' + side]
    for c in spec['elbow']:
        comp_part[c] = PART['Elbow_' + side]
    for c in spec['disc']:
        comp_part[c] = PART['Disc_' + side]
    for c in spec['cable']:
        comp_part[c] = PART['Elbow_' + side]          # face part for UV/material grouping; weights blended below
for c in SENSOR_HEAD:
    comp_part[c] = PART['Sensor']
comp_part[sizes < 12] = -1
cable_comp = {c: side for side, spec in (('L', LEFT), ('R', RIGHT)) for c in spec['cable']}

M = Matrix.Scale(SCALE, 4) @ Matrix.Translation(-CENTRE)
fpart = bm.faces.layers.int.new('part')
fcable = bm.faces.layers.int.new('cable')            # 0 none, 1 left, 2 right
for f in bm.faces:
    c = labels[f.verts[0].index]
    f[fpart] = comp_part[c]
    f[fcable] = {'L': 1, 'R': 2}.get(cable_comp.get(c), 0)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[fpart] < 0], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
for v in bm.verts:
    v.co = M @ v.co
zmin = min(v.co.z for v in bm.verts)
for v in bm.verts:
    v.co.z -= zmin
joints = {k: list((M @ Vector(p)) - Vector((0, 0, zmin))) for k, p in RAW_JOINTS.items()}
joints['Body'] = [0.0, 0.0, -zmin]
names = ['Root', 'Body', 'Sensor', 'Shoulder_L', 'Elbow_L', 'Disc_L', 'Shoulder_R', 'Elbow_R', 'Disc_R']
gi = {n: i for i, n in enumerate(names)}


def chain_weights(p, side):
    """Weights along shoulder -> elbow -> hub for a cable vertex: nearest point on the polyline (t 0 shoulder,
    1 elbow, 2 hub), a blend Body -> Shoulder at the mount, Shoulder -> Elbow around the elbow."""
    s, e, h = (Vector(joints[f'{k}_{side}']) for k in ('Shoulder', 'Elbow', 'Disc'))
    best = None
    for a, b, t0 in ((s, e, 0.0), (e, h, 1.0)):
        ab = b - a; u = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
        d = (p - (a + ab * u)).length
        if best is None or d < best[0]:
            best = (d, t0 + u)
    t = best[1]
    sh, el = gi['Shoulder_' + side], gi['Elbow_' + side]
    if t < 0.15:
        return {gi['Body']: 1.0 - t / 0.15, sh: t / 0.15}
    if t < 0.8:
        return {sh: 1.0}
    if t < 1.2:
        w = (t - 0.8) / 0.4
        return {sh: 1.0 - w, el: w}
    return {el: 1.0}


for p in range(1, 9):
    faces = [f for f in bm.faces if f[fpart] == p]
    bmesh.ops.remove_doubles(bm, verts=list({v for f in faces for v in f.verts}), dist=0.0001)
    faces = [f for f in bm.faces if f[fpart] == p]
    bmesh.ops.recalc_face_normals(bm, faces=faces)
weights = {}
for f in bm.faces:
    for v in f.verts:
        if f[fcable]:
            weights[v.index] = chain_weights(v.co, 'L' if f[fcable] == 1 else 'R')
        elif v.index not in weights:
            weights[v.index] = {f[fpart]: 1.0}
bm.to_mesh(obj.data); bm.free()
obj.vertex_groups.clear()
for n in names:
    obj.vertex_groups.new(name=n)
for vi, w in weights.items():
    for g, x in w.items():
        if x > 0:
            obj.vertex_groups[g].add([vi], x, 'REPLACE')
counts = {}
for poly, value in zip(obj.data.polygons, obj.data.attributes['part'].data):
    counts[names[value.value]] = counts.get(names[value.value], 0) + len(poly.vertices) - 2
obj['joints'] = json.dumps(joints)
co = np.array([v.co[:] for v in obj.data.vertices])
print('PART_TRIS', json.dumps(counts), 'total', sum(counts.values()))
print('BOUNDS', co.min(0).round(3), co.max(0).round(3))
print('JOINTS', json.dumps({k: [round(x, 3) for x in v] for k, v in joints.items()}))
os.makedirs(cc.path('work'), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=cc.path('work/parts.blend'))
print('SAVED')
