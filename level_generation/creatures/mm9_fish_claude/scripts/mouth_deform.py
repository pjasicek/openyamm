"""Bring the mouth to the master's proportions by a soft deform of 'Body' (no topology or UV change, so the retexture
stays valid). About the mouth axis (x = 0, z = ZA): x scales by SX and z by SZ.
- Cavity vertices (a ray outward from the axis meets the body again) take the full scale, so the tube stays closed.
- Lip and snout skin take it by a radial falloff (full inside R1, none past R2) times a falloff along the head (full to
  8 mm behind the lips, none past 20 mm above the mouth, so the eyes keep their skin, and none past 36 mm under it, so
  the chin does not step). The axis sits 3 mm under the mouth's centre: the upper lip travels more than the lower.
- Eye lenses move rigidly with the skin under their centre.
Args: <in blend> <out blend> <sx> <sz>"""
import bpy, sys, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, SX, SZ = argv[0], argv[1], float(argv[2]), float(argv[3])
ZA, R1, R2, Y1, Y2, Y2_CHIN = 0.0605, 0.017, 0.032, 0.008, 0.020, 0.036
bpy.ops.wm.open_mainfile(filepath=IN)
b = bpy.data.objects['Body']; me = b.data
pa = me.attributes['piece']
faces = [p for p in me.polygons if pa.data[p.index].value == 0]
piece = np.zeros(len(me.vertices), int)
for p in me.polygons:
    if pa.data[p.index].value:
        piece[list(p.vertices)] = 1
tree = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(p.vertices) for p in faces])
P = np.array([tuple(v.co) for v in me.vertices])
ymin = P[piece == 0, 1].min()


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def weight(p):
    r = np.hypot(p[..., 0], p[..., 2] - ZA)
    y2 = Y2 + (Y2_CHIN - Y2) * (1 - smooth(ZA - 0.002, ZA + 0.008, p[..., 2]))    # the chin fades further back
    return (1 - smooth(R1, R2, r)) * (1 - smooth(ymin + Y1, ymin + y2, p[..., 1]))


W = np.zeros(len(P))
cav = 0
for i in np.nonzero(piece == 0)[0]:
    p = P[i]
    if p[1] > ymin + 0.06:
        continue
    d = Vector((p[0], 0, p[2] - ZA))
    if d.length < 1e-6:
        W[i] = 1; cav += 1; continue
    d.normalize()
    hit = tree.ray_cast(Vector(p) + d * 2e-4, d, 0.05)
    # inside the cavity: more body outward, and that body is well outside this vertex
    if hit[0] is not None and hit[3] > 0.003 and np.hypot(p[0], p[2] - ZA) < R2:
        W[i] = 1; cav += 1
    else:
        W[i] = float(weight(p))
Q = P.copy()
Q[:, 0] = P[:, 0] * (1 - W * (1 - SX))
Q[:, 2] = ZA + (P[:, 2] - ZA) * (1 - W * (1 - SZ))
for side in (1, -1):
    ids = np.nonzero((piece == 1) & (np.sign(P[:, 0]) == side))[0]
    c = P[ids].mean(0)
    w = float(weight(c))
    Q[ids, 0] += c[0] * -w * (1 - SX)
    Q[ids, 2] += (c[2] - ZA) * -w * (1 - SZ)
for i, v in enumerate(me.vertices):
    v.co = Vector(Q[i])
print('DEFORM', json.dumps({'cavity': cav, 'moved': int((W > 0).sum()), 'max_move_mm': float(np.linalg.norm(Q - P, axis=1).max() * 1000)}))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
